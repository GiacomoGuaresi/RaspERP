# app/routes/inventory.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.utils import query_db, get_db, log_action
import re
import datetime

inventory_bp = Blueprint("inventory", __name__)

@inventory_bp.route('/Inventory')
def view_Inventory():
    data = query_db('SELECT * FROM Inventory')
    return render_template('Inventory.html', data=data)

@inventory_bp.route('/Inventory/increase/<ProductCode>')
def increase_Inventory(ProductCode):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'UPDATE Inventory SET QuantityOnHand = QuantityOnHand + 1 WHERE ProductCode = ?', (ProductCode,))
    db.commit()
    return redirect(url_for('inventory.view_Inventory'))

@inventory_bp.route('/Inventory/decrease/<ProductCode>')
def decrease_Inventory(ProductCode):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT QuantityOnHand FROM Inventory WHERE ProductCode = ?', (ProductCode,))
    row = cursor.fetchone()

    if row and row[0] > 0:
        cursor.execute('UPDATE Inventory SET QuantityOnHand = QuantityOnHand - 1 WHERE ProductCode = ?', (ProductCode,))
        db.commit()

    return redirect(url_for('inventory.view_Inventory'))


# Variabili temporanee per l'ultimo codice e il suo conteggio (persi al refresh)
last_scanned = None
last_added_count = 0
last_moment = None
last_direction = None

@inventory_bp.route('/Inventory/codereader', methods=['GET', 'POST'])
def codereader_Inventory():
    global last_scanned, last_added_count, last_moment, last_direction

    db = get_db()
    cursor = db.cursor()
    last_Product = None
    error = None

    if request.method == 'POST':
        raw_code = request.form.get('ProductCode', '').strip().upper()  # Case insensitive

        # Controlla se è un modificatore (MOD>Xn)
        mod_match = re.match(r"^MOD>X(\d+)$", raw_code)
        if mod_match:
            newQuanity = last_added_count + int(mod_match.group(1))
            last_moment = datetime.datetime.now()
            cursor.execute("SELECT QuantityOnHand FROM Inventory WHERE ProductCode = ?", (last_scanned,))
            row = cursor.fetchone()

            if last_direction == "IN":
                cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand + ? WHERE ProductCode = ?", 
                               (newQuanity - last_added_count, last_scanned,))
                log_action(cursor, f"Added {newQuanity - last_added_count} units of {last_scanned}", "BARCODEREADER")

            elif last_direction == "OUT":
                if row and (row["QuantityOnHand"] - row["Locked"]) >= newQuanity - last_added_count:
                    cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand - ? WHERE ProductCode = ?", 
                                   (newQuanity - last_added_count, last_scanned,))
                    log_action(cursor, f"Removed {newQuanity - last_added_count} units of {last_scanned}", "BARCODEREADER")
                else:
                    error = "Unable to extract the part from the stock, unavailable or stuck"
            
            elif last_direction == "WORK":
                if row and row["Locked"] >= newQuanity - last_added_count:
                    cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand - ?, Locked = Locked - ? WHERE ProductCode = ?", 
                                   (newQuanity - last_added_count, newQuanity - last_added_count, last_scanned,))
                    log_action(cursor, f"Working {newQuanity - last_added_count} units of {last_scanned}", "BARCODEREADER")
                else:
                    error = "Unable to extract the part from the stock, unavailable or stuck"

            db.commit()

            # Recupera l'ultimo prodotto aggiornato
            cursor.execute("SELECT * FROM Inventory WHERE ProductCode = ?", (last_scanned,))
            last_Product = cursor.fetchone()
            last_added_count = newQuanity

        # Controlla se è un codice Inventory (IN>, OUT>, WORK>)
        match = re.match(r"^(IN|OUT|WORK)>(\w+)$", raw_code)
        if match:
            action, Product_code = match.groups()

            if last_moment is None:
                last_moment = datetime.datetime.now()

            if last_scanned != Product_code or last_direction != action or (datetime.datetime.now() - last_moment).total_seconds() > 60:
                last_added_count = 0

            last_scanned = Product_code  
            last_added_count += 1  
            last_moment = datetime.datetime.now()
            last_direction = action

            cursor.execute("SELECT QuantityOnHand, Locked FROM Inventory WHERE ProductCode = ?", (Product_code,))
            row = cursor.fetchone()

            if action == "IN":
                if row:
                    cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand + 1 WHERE ProductCode = ?", 
                                   (Product_code,))
                else:
                    cursor.execute("INSERT INTO Inventory (ProductCode, QuantityOnHand) VALUES (?, 1)", 
                                   (Product_code,))
                log_action(cursor, f"Added 1 unit of {Product_code}", "BARCODEREADER")

            elif action == "OUT":
                if row and (row["QuantityOnHand"] - row["Locked"]) > 0:
                    cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand - 1 WHERE ProductCode = ?", 
                                   (Product_code,))
                    log_action(cursor, f"Removed 1 unit of {Product_code}", "BARCODEREADER")
                else:
                    error = "Unable to extract the part from the stock, unavailable or stuck"
            
            elif action == "WORK":
                if row and row["Locked"] > 0:
                    cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand - 1, Locked = Locked - 1 WHERE ProductCode = ?", 
                                   (Product_code,))
                    log_action(cursor, f"Working 1 unit of {Product_code}", "BARCODEREADER")
                else:
                    error = "Unable to extract the part from the stock, unavailable or stuck"
            db.commit()

            # Recupera l'ultimo prodotto aggiornato
            cursor.execute("SELECT * FROM Inventory WHERE ProductCode = ?", (Product_code,))
            last_Product = cursor.fetchone()

    return render_template('Inventory_codereader.html', last_item=last_Product, last_added_count=last_added_count, error=error)

