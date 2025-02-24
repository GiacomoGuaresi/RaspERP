from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import datetime
from datetime import date 
import re

app = Flask(__name__)
DB_NAME = 'database.db'
# Cambia se il tuo file si chiama diversamente
app.config['DATABASE'] = DB_NAME

def log_action(cursor, message, user):
    """Inserisce un messaggio di log nel database."""
    cursor.execute("INSERT INTO logs (message, user) VALUES (?, ?)", (message, user, ))

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row  # Per ottenere i risultati come dizionario-like
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Home Page


@app.route('/')
def index():
    return render_template('index.html')

# Utility function to query database


def query_db(query, args=(), one=False):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        conn.commit()
    return (rv[0] if rv else None) if one else rv

# BillOfMaterials Routes


@app.route('/BillOfMaterials')
def view_BillOfMaterials():
    data = query_db('SELECT * FROM BillOfMaterials')
    return render_template('BillOfMaterials.html', data=data)


@app.route('/BillOfMaterials/add', methods=['GET', 'POST'])
def add_BillOfMaterials():
    if request.method == 'POST':
        query_db('INSERT INTO BillOfMaterials (ProductCode, ChildProductCode, Quantity) VALUES (?, ?, ?)',
                 (request.form['ProductCode'], request.form['ChildProductCode'], int(request.form['Quantity'])))
        return redirect(url_for('view_BillOfMaterials'))
    
    product_codes = query_db('SELECT ProductCode FROM Product')
    return render_template('BillOfMaterials_add.html', product_codes=product_codes)


@app.route('/BillOfMaterials/delete/<ProductCode>')
def delete_BillOfMaterials(ProductCode):
    query_db('DELETE FROM BillOfMaterials WHERE BillOfMaterialID = ?', (ProductCode,))
    return redirect(url_for('view_BillOfMaterials'))

# ProductionOrder Routes


@app.route('/ProductionOrder')
def view_ProductionOrder():
    data = query_db('SELECT * FROM ProductionOrder')
    return render_template('ProductionOrder.html', data=data)


@app.route('/ProductionOrder/add', methods=['GET', 'POST'])
def add_ProductionOrder():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()

        orderDate = request.form['OrderDate']
        code = request.form['ProductCode']
        quantity = int(request.form['Quantity'])

        # Inserisce la ProductionOrdere principale
        cursor.execute(
            'INSERT INTO ProductionOrder (OrderDate, ProductCode, Quantity) VALUES (?, ?, ?)',
            (orderDate, code, quantity)
        )
        inserted_id = cursor.lastrowid

        # Cerca i componenti nella BillOfMaterials
        cursor.execute(
            'SELECT ChildProductCode, Quantity FROM BillOfMaterials WHERE ProductCode = ?',
            (code,)
        )
        components = cursor.fetchall()

        for component_code, component_quantity in components:
            total_quantity = quantity * component_quantity

            cursor.execute("SELECT * FROM Inventory WHERE ProductCode = ?", (component_code,))
            item = cursor.fetchone()

            if item is not None:
                available = item[1] - item[2]
                if available > total_quantity: 
                    used = total_quantity
                else:
                    used = available
            else: 
                used = 0

            cursor.execute(
                'INSERT INTO ProductionOrderProgress (OrderID, ProductCode, QuantityRequired, QuantityCompleted) VALUES (?, ?, ?, ?)',
                (inserted_id, component_code, total_quantity, used)
            )

            if used > 0:
                cursor.execute(
                    'UPDATE Inventory SET Locked = Locked + ? WHERE ProductCode = ?',
                    (used, component_code,)
                )
            
            db.commit()

        db.commit()
        return redirect(url_for('view_ProductionOrder'))
        
    orderDate = request.args.get('date', date.today().isoformat())
    code = request.args.get('code', '')
    quantity = request.args.get('quantity', '')

    product_codes = query_db('SELECT ProductCode FROM Product')

    return render_template('ProductionOrder_add.html', OrderDate=orderDate, ProductCode=code, Quantity=quantity, product_codes=product_codes)


@app.route('/ProductionOrder/delete/<OrderID>')
def delete_ProductionOrder(OrderID):
    query_db('DELETE FROM ProductionOrder WHERE OrderID = ?', (OrderID,))
    query_db('DELETE FROM ProductionOrderProgress WHERE OrderID = ?', (OrderID,))
    return redirect(url_for('view_ProductionOrder'))


@app.route('/ProductionOrder/complete/<OrderID>')
def complete_ProductionOrder(OrderID):
    query_db('UPDATE ProductionOrder SET Status = ? WHERE OrderID = ?',
             ("Complete", OrderID))
    return redirect(url_for('view_ProductionOrder'))


# ProductionOrderProgress Routes
@app.route('/ProductionOrderProgress/<int:OrderID>')
def view_ProductionOrderProgress(OrderID):
    data = query_db("""
                    SELECT ProductionOrderProgress.*, Product.*, ProductionOrder.OrderID as childOrderId FROM ProductionOrderProgress 
                    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode 
                    LEFT JOIN ProductionOrder ON ProductionOrder.ParentOrderID = ProductionOrderProgress.OrderID AND ProductionOrder.ProductCode = ProductionOrderProgress.ProductCode
                    WHERE ProductionOrderProgress.OrderID = ?
                    """, (OrderID,))
    order = query_db('SELECT * FROM ProductionOrder WHERE OrderID = ?', (OrderID, ))[0]
    return render_template('ProductionOrderProgress.html', data=data, current_date=date.today().isoformat(), order=order)


@app.route('/ProductionOrderProgress/increase/<int:ProgressID>')
def increase_ProductionOrderProgress(ProgressID):
    OrderID = request.args.get('OrderID', type=int)
    db = get_db()
    cursor = db.cursor()

    # Recupera il valore attuale di QuantityCompleted
    cursor.execute(
        'SELECT QuantityCompleted, QuantityRequired FROM ProductionOrderProgress WHERE ProgressID = ?', (ProgressID,))
    row = cursor.fetchone()

    if row:
        quantity_present, quantity_required = row
        # Incrementa QuantityCompleted solo se non supera il massimo richiesto
        if quantity_present < quantity_required:
            cursor.execute(
                'UPDATE ProductionOrderProgress SET QuantityCompleted = QuantityCompleted + 1 WHERE ProgressID = ?',
                (ProgressID,)
            )
            db.commit()

    return redirect(url_for('view_ProductionOrderProgress', OrderID=OrderID))


@app.route('/ProductionOrderProgress/decrease/<int:ProgressID>')
def decrease_ProductionOrderProgress(ProgressID):
    OrderID = request.args.get('OrderID', type=int)
    db = get_db()
    cursor = db.cursor()

    # Recupera il valore attuale di QuantityCompleted
    cursor.execute(
        'SELECT QuantityCompleted FROM ProductionOrderProgress WHERE ProgressID = ?', (ProgressID,))
    row = cursor.fetchone()

    if row:
        quantity_present = row[0]
        # Decrementa QuantityCompleted solo se è maggiore di 0
        if quantity_present > 0:
            cursor.execute(
                'UPDATE ProductionOrderProgress SET QuantityCompleted = QuantityCompleted - 1 WHERE ProgressID = ?',
                (ProgressID,)
            )
            db.commit()

    return redirect(url_for('view_ProductionOrderProgress', OrderID=OrderID))


# Product Routes
@app.route('/Product')
def view_Product():
    data = query_db('SELECT * FROM Product')
    return render_template('Product.html', data=data)


@app.route('/Product/add', methods=['GET', 'POST'])
def add_Product():
    if request.method == 'POST':
        try:
            query_db('INSERT INTO Product (ProductCode, Category) VALUES (?, ?)',
                    (request.form['ProductCode'], request.form['Category']))
            return redirect(url_for('view_Product'))
        except:
            return render_template('Product_add.html', message='the product ' + request.form['ProductCode'] + ' is already present in the database')        
    return render_template('Product_add.html')


@app.route('/Product/delete/<code>')
def delete_Product(code):
    query_db('DELETE FROM Product WHERE ProductCode = ?', (code,))
    return redirect(url_for('view_Product'))


#  Inventory Routes
@app.route('/Inventory')
def view_Inventory():
    data = query_db('SELECT * FROM Inventory')
    return render_template('Inventory.html', data=data)


@app.route('/Inventory/increase/<ProductCode>')
def increase_Inventory(ProductCode):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'UPDATE Inventory SET QuantityOnHand = QuantityOnHand + 1 WHERE ProductCode = ?', (ProductCode,))
    db.commit()
    return redirect(url_for('view_Inventory'))


@app.route('/Inventory/decrease/<ProductCode>')
def decrease_Inventory(ProductCode):
    db = get_db()
    cursor = db.cursor()

    # Recupera il valore attuale di QuantityCompleted
    cursor.execute(
        'SELECT QuantityOnHand FROM Inventory WHERE ProductCode = ?', (ProductCode,))
    row = cursor.fetchone()

    if row:
        quantity = row[0]
        if quantity > 0:
            cursor.execute(
                'UPDATE Inventory SET QuantityOnHand = QuantityOnHand - 1 WHERE ProductCode = ?',
                (ProductCode,)
            )
            db.commit()

    return redirect(url_for('view_Inventory'))


# Variabili temporanee per l'ultimo codice e il suo conteggio (persi al refresh)
last_scanned = None
last_added_count = 0
last_moment = None
last_direction = None

@app.route('/Inventory/codereader', methods=['GET', 'POST'])
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


if __name__ == '__main__':
    app.run(debug=True)


# def recursiveProgressEntry(code):
