# app/routes/inventory.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.utils import query_db, get_db, log_action
import re
import datetime
from collections import defaultdict
from flask_login import login_required

inventory_bp = Blueprint("inventory", __name__)


def group_by_category(data):
    grouped = defaultdict(list)
    for item in data:
        grouped[item['Category']].append(item)
    return grouped


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
    ordersOnGoing = query_db("""SELECT Product.Category, ProductionOrderProgress.ProductCode, SUM(ProductionOrderProgress.QuantityRequired) as QuantityRequired, SUM(ProductionOrderProgress.QuantityCompleted) as QuantityCompleted
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status IS "On Going" 
	AND Product.Category IS NOT "Subassembly"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted
	GROUP BY ProductionOrderProgress.ProductCode""")

    ordersPlanned = query_db("""SELECT Product.Category, ProductionOrderProgress.ProductCode, SUM(ProductionOrderProgress.QuantityRequired) as QuantityRequired, SUM(ProductionOrderProgress.QuantityCompleted) as QuantityCompleted
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status IS "Planned" 
	AND Product.Category IS NOT "Subassembly"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted
	GROUP BY ProductionOrderProgress.ProductCode""")

    grouped_ongoing = group_by_category(ordersOnGoing)
    grouped_planned = group_by_category(ordersPlanned)

    return render_template("inventory_missingParts.html", grouped_orders_ongoing=grouped_ongoing, grouped_orders_planned=grouped_planned)


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
        SELECT ProgressID, QuantityRequired, ProductionOrderProgress.QuantityCompleted 
        FROM ProductionOrderProgress 
        JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
        WHERE Status = "On Going"
        AND ProductionOrderProgress.QuantityCompleted < ProductionOrderProgress.QuantityRequired
        AND ProductionOrderProgress.ProductCode = ?
    """, (ProductCode,))
    neededOrder = cursor.fetchone()

    if neededOrder:
        progressId = neededOrder["ProgressID"]
        qty_required = neededOrder["QuantityRequired"]
        qty_completed = neededOrder["QuantityCompleted"]
        needed_qty = qty_required - qty_completed

        to_use = min(delta, needed_qty)
        remaining = delta - to_use

        # Aggiorna ProductionOrderProgress
        cursor.execute("""
            UPDATE ProductionOrderProgress 
            SET QuantityCompleted = QuantityCompleted + ? 
            WHERE ProgressID = ?
        """, (to_use, progressId))

        # Aggiorna ProductionOrder
        cursor.execute("""
            SELECT OrderID, Quantity, QuantityCompleted 
            FROM ProductionOrder 
            WHERE Status = "On Going" 
            AND ProductCode = ?
            AND QuantityCompleted < Quantity
        """, (ProductCode,))
        order = cursor.fetchone()

        if order:
            order_needed = order["Quantity"] - order["QuantityCompleted"]
            to_use_order = min(to_use, order_needed)  # per sicurezza
            cursor.execute("""
                UPDATE ProductionOrder 
                SET QuantityCompleted = QuantityCompleted + ? 
                WHERE OrderID = ?
            """, (to_use_order, order["OrderID"]))

        # Aggiorna inventario
        cursor.execute("""
            UPDATE Inventory 
            SET QuantityOnHand = QuantityOnHand + ?, 
                Locked = Locked + ? 
            WHERE ProductCode = ?
        """, (delta, to_use, ProductCode))

        log_action(
            f"Added {delta} unit(s) of {ProductCode}: {to_use} locked for production progress {progressId}, {remaining} available.")
    else:
        # Nessun ordine in corso -> solo disponibile
        cursor.execute("""
            UPDATE Inventory 
            SET QuantityOnHand = QuantityOnHand + ? 
            WHERE ProductCode = ?
        """, (delta, ProductCode))
        log_action(f"Added {delta} unit(s) of {ProductCode} (all available)")

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

    cursor.execute(
        "SELECT QuantityOnHand, Locked FROM Inventory WHERE ProductCode = ?", (ProductCode,))
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