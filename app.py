from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import date
import re

app = Flask(__name__)
DB_NAME = 'database.db'
# Cambia se il tuo file si chiama diversamente
app.config['DATABASE'] = DB_NAME
app.secret_key = "barcodeReader"  # Per gestire sessioni utente


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
    query_db('DELETE FROM BillOfMaterials WHERE ProductCode = ?', (ProductCode,))
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
            cursor.execute(
                'INSERT INTO ProductionOrderProgress (OrderID, ProductCode, QuantityRequired, QuantityCompleted) VALUES (?, ?, ?, ?)',
                (inserted_id, component_code, total_quantity, 0)
            )

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
    data = query_db('SELECT ProductionOrderProgress.*, Product.* FROM ProductionOrderProgress JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode WHERE ProductionOrderProgress.OrderID = ?', (OrderID,))
    return render_template('ProductionOrderProgress.html', data=data, current_date=date.today().isoformat(), id=OrderID)


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
        query_db('INSERT INTO Product (ProductCode, Category) VALUES (?, ?)',
                 (request.form['ProductCode'], request.form['Category']))
        return redirect(url_for('view_Product'))
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


@app.route('/Inventory/codereader', methods=['GET', 'POST'])
def codereader_Inventory():
    global last_scanned, last_added_count

    db = get_db()
    cursor = db.cursor()

    last_Product = None  # Dati dell'ultimo prodotto aggiornato

    if request.method == 'POST':
        raw_code = request.form.get('ProductCode', '').strip().upper()  # Case insensitive

        # Controlla se è un modificatore (MOD>Xn)
        mod_match = re.match(r"^MOD>X(\d+)$", raw_code)
        if mod_match:
            multiplier = int(mod_match.group(1))
            if last_scanned:
                last_added_count *= multiplier  # Moltiplica il conteggio precedente
            return render_template('Inventory_codereader.html', last_item=last_Product, last_added_count=last_added_count)

        # Controlla se è un codice Inventory (IN>, OUT>, WORK>)
        match = re.match(r"^(IN|OUT|WORK)>(\w+)$", raw_code)
        if match:
            action, Product_code = match.groups()

            # Se il nuovo codice è diverso dall'ultimo, resetta il contatore
            if last_scanned != Product_code:
                last_added_count = 0

            last_scanned = Product_code  # Memorizza l'ultimo codice
            last_added_count += 1  # Incrementa il contatore solo per l'ultimo inserito

            # Controlla se il prodotto esiste in Inventory
            cursor.execute("SELECT QuantityOnHand FROM Inventory WHERE ProductCode = ?", (Product_code,))
            row = cursor.fetchone()

            if action == "IN":
                if row:
                    cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand + 1 WHERE ProductCode = ?", (Product_code,))
                else:
                    cursor.execute("INSERT INTO Inventory (ProductCode, QuantityOnHand) VALUES (?, 1)", (Product_code,))

            elif action in ["OUT", "WORK"]:
                if row and row["QuantityOnHand"] > 0:  # row["QuantityOnHand"] funziona grazie a row_factory
                    cursor.execute("UPDATE Inventory SET QuantityOnHand = QuantityOnHand - 1 WHERE ProductCode = ?", (Product_code,))

            db.commit()

            # Recupera l'ultimo prodotto aggiornato
            cursor.execute("SELECT * FROM Inventory WHERE ProductCode = ?", (Product_code,))
            last_Product = cursor.fetchone()

    return render_template('Inventory_codereader.html', last_item=last_Product, last_added_count=last_added_count)


if __name__ == '__main__':
    app.run(debug=True)


# def recursiveProgressEntry(code):
