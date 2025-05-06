# app/routes/inventory.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.utils import query_db, get_db, log_action
import re
import datetime
from collections import defaultdict
from flask_login import login_required

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route('/Inventory')
@login_required
def view_Inventory():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    error = request.args.get('error', '')
    data = query_db(
        'SELECT * FROM Inventory LEFT JOIN Product ON Product.ProductCode = Inventory.ProductCode ORDER BY Inventory.ProductCode ASC')
    return render_template('Inventory.html', data=data, selected_category=category, search_text=search, error=error)

@inventory_bp.route('/Inventory/missingParts')
@login_required
def missingParts_Inventory():
    ordersOnGoing = query_db("""SELECT ProductionOrderProgress.*, Product.Category, ProductionOrder.ProductCode as OrderProductCode 
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status = "On Going"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted""")

    ordersPlanned = query_db("""SELECT ProductionOrderProgress.*, Product.Category, Product.Image, ProductionOrder.ProductCode as OrderProductCode 
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status = "Planned"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted""")

    # Raggruppa ordersOnGoing per OrderProductCode
    grouped_orders_ongoing = defaultdict(list)
    for row in ordersOnGoing:
        grouped_orders_ongoing[row["OrderProductCode"]].append(row)

    # Raggruppa ordersPlanned per OrderProductCode
    grouped_orders_planned = defaultdict(list)
    for row in ordersPlanned:
        grouped_orders_planned[row["OrderProductCode"]].append(row)

    return render_template("inventory_missingParts.html", grouped_orders_ongoing=grouped_orders_ongoing, grouped_orders_planned=grouped_orders_planned)
    
@inventory_bp.route('/Inventory/increase/<ProductCode>')
@login_required
def increase_Inventory(ProductCode):
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    delta = int(request.args.get('delta', 1))  # valore arbitrario

    increase_Inventory(ProductCode, delta)
    return redirect(url_for('inventory.view_Inventory', category=category, search=search))

def increase_Inventory(ProductCode, delta):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT ProgressID FROM ProductionOrderProgress 
        JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
        WHERE Status = "On Going"
        AND ProductionOrderProgress.QuantityCompleted < ProductionOrderProgress.QuantityRequired
        AND ProductionOrderProgress.ProductCode = ?
    """, (ProductCode,))
    neededOrders = cursor.fetchone()

    if neededOrders:
        progressId = neededOrders["ProgressID"]
        cursor.execute("""
            UPDATE ProductionOrderProgress 
            SET QuantityCompleted = QuantityCompleted + ? 
            WHERE ProgressID = ?
        """, (delta, progressId))

        cursor.execute("""
            SELECT OrderID FROM ProductionOrder 
            WHERE Status = "On Going" 
            AND QuantityCompleted < Quantity 
            AND ProductCode = ?
        """, (ProductCode,))
        order = cursor.fetchone()

        if order:
            cursor.execute("""
                UPDATE ProductionOrder 
                SET QuantityCompleted = QuantityCompleted + ? 
                WHERE OrderID = ?
            """, (delta, order["OrderID"]))

        cursor.execute("""
            UPDATE Inventory 
            SET QuantityOnHand = QuantityOnHand + ?, Locked = Locked + ? 
            WHERE ProductCode = ?
        """, (delta, delta, ProductCode))

        log_action(f"Added {delta} unit(s) of {ProductCode} for production progress {progressId}")
    else:
        cursor.execute("""
            UPDATE Inventory 
            SET QuantityOnHand = QuantityOnHand + ? 
            WHERE ProductCode = ?
        """, (delta, ProductCode))
        log_action(f"Added {delta} unit(s) of {ProductCode}")

    db.commit()

@inventory_bp.route('/Inventory/decrease/<ProductCode>')
@login_required
def decrease_Inventory(ProductCode):
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    delta = int(request.args.get('delta', 1))  # valore arbitrario

    db = get_db()
    cursor = db.cursor()
    error = ""

    cursor.execute("SELECT QuantityOnHand, Locked FROM Inventory WHERE ProductCode = ?", (ProductCode,))
    row = cursor.fetchone()

    if row and (row["QuantityOnHand"] - row["Locked"]) >= delta:
        cursor.execute("""
            UPDATE Inventory 
            SET QuantityOnHand = QuantityOnHand - ? 
            WHERE ProductCode = ?
        """, (delta, ProductCode))
        log_action(f"Removed {delta} unit(s) of {ProductCode}")
    else:
        error = "Unable to extract the part from stock: not enough available quantity"

    db.commit()
    return redirect(url_for('inventory.view_Inventory', category=category, search=search, error=error))


# Variabili temporanee per l'ultimo codice e il suo conteggio (persi al refresh)
last_scanned = None
last_added_count = 0
last_moment = None
last_direction = None


@inventory_bp.route('/Inventory/codereader', methods=['GET', 'POST'])
@login_required
def codereader_Inventory():
    global last_scanned, last_added_count, last_moment, last_direction

    db = get_db()
    cursor = db.cursor()
    last_Product = None
    error = None
    action = None

    if request.method == 'POST':
        Product_code = request.form.get(
            'ProductCode', '').strip().upper()  # Case insensitive
        action = request.form.get(
            'action', '').strip().upper()  # Case insensitive

        # TODO: call the in or out or work function X time
        # Controlla se è un modificatore (MOD>Xn)
        # mod_match = re.match(r"^MOD>X(\d+)$", raw_code)
        # if mod_match:

        # Controlla se è un codice Inventory (IN>, OUT>, WORK>)

        if last_moment is None:
            last_moment = datetime.datetime.now()

        if last_scanned != Product_code or last_direction != action or (datetime.datetime.now() - last_moment).total_seconds() > 60:
            last_added_count = 0

        last_scanned = Product_code
        last_added_count += 1
        last_moment = datetime.datetime.now()
        last_direction = action

        cursor.execute(
            "SELECT QuantityOnHand, Locked FROM Inventory WHERE ProductCode = ?", (Product_code,))
        row = cursor.fetchone()

        if action == "IN":

            # Check if this item is necessary for a commission
            cursor.execute("""SELECT ProgressID FROM ProductionOrderProgress 
                JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID

                WHERE Status IS "On Going"
                AND ProductionOrderProgress.QuantityCompleted < ProductionOrderProgress.QuantityRequired
                AND ProductionOrderProgress.ProductCode IS ?""", (Product_code,))
            neededOrders = cursor.fetchone()

            if neededOrders:
                progressId = neededOrders["ProgressID"]
                cursor.execute(
                    "UPDATE ProductionOrderProgress SET QuantityCompleted = QuantityCompleted + 1 WHERE ProgressID = ?", (progressId,))

                cursor.execute(
                    """SELECT OrderID FROM ProductionOrder 
                    WHERE Status IS "On Going" 
                    AND ProductionOrder.QuantityCompleted < ProductionOrder.Quantity 
                    AND ProductCode IS ?""", (Product_code,))
                neededOrders = cursor.fetchone()
                if neededOrders:
                    orderId = neededOrders["OrderID"]
                    cursor.execute(
                        "UPDATE ProductionOrder SET QuantityCompleted = QuantityCompleted + 1 WHERE OrderId = ?", (orderId,))

                cursor.execute(
                    "UPDATE Inventory SET QuantityOnHand = QuantityOnHand + 1, Locked = Locked + 1 WHERE ProductCode = ?", (Product_code,))
                log_action(
                    f"Added 1 unit of {Product_code} and used for production order progress {progressId}")
            else:
                cursor.execute(
                    "UPDATE Inventory SET QuantityOnHand = QuantityOnHand + 1 WHERE ProductCode = ?", (Product_code,))
                log_action(
                    f"Added 1 unit of {Product_code}")

        elif action == "OUT":
            if row and (row["QuantityOnHand"] - row["Locked"]) > 0:
                cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand - 1 WHERE ProductCode = ?",
                               (Product_code,))
                log_action(
                    f"Removed 1 unit of {Product_code}", "BARCODEREADER")
            else:
                error = "Unable to extract the part from the stock, unavailable or stuck"

        elif action == "WORK":
            if row and row["Locked"] > 0:
                cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand - 1, Locked = Locked - 1 WHERE ProductCode = ?",
                               (Product_code,))
                log_action(
                    f"Working 1 unit of {Product_code}")
            else:
                error = "Unable to extract the part from the stock, unavailable or stuck"
        db.commit()

        # Recupera l'ultimo prodotto aggiornato
        cursor.execute(
            "SELECT Inventory.*, Product.Image FROM Inventory LEFT JOIN Product ON Product.ProductCode = Inventory.ProductCode WHERE Inventory.ProductCode = ?", (Product_code,))
        last_Product = cursor.fetchone()

    return render_template('Inventory_codereader.html', last_item=last_Product, last_added_count=last_added_count, error=error, action=action)
