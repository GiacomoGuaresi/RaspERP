from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import date
import re

app = Flask(__name__)
DB_NAME = 'database.db'
app.config['DATABASE'] = DB_NAME  # Cambia se il tuo file si chiama diversamente
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

# BOM Routes
@app.route('/bom')
def view_bom():
    data = query_db('SELECT * FROM BOM')
    return render_template('bom.html', data=data)

@app.route('/bom/add', methods=['GET', 'POST'])
def add_bom():
    if request.method == 'POST':
        query_db('INSERT INTO BOM (Code, ComponentCode, Quantity) VALUES (?, ?, ?)',
                 (request.form['Code'], request.form['ComponentCode'], int(request.form['Quantity'])))
        return redirect(url_for('view_bom'))
    return render_template('bom_add.html')

@app.route('/bom/delete/<code>')
def delete_bom(code):
    query_db('DELETE FROM BOM WHERE Code = ?', (code,))
    return redirect(url_for('view_bom'))

# Commission Routes
@app.route('/commission')
def view_commission():
    data = query_db('SELECT * FROM Commission')
    return render_template('commission.html', data=data)

@app.route('/commission/add', methods=['GET', 'POST'])
def add_commission():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()

        date = request.form['date']
        code = request.form['code']
        quantity = int(request.form['quantity'])

        # Inserisce la commissione principale
        cursor.execute(
            'INSERT INTO Commission (Date, Code, Quantity) VALUES (?, ?, ?)',
            (date, code, quantity)
        )
        inserted_id = cursor.lastrowid

        # Cerca i componenti nella BOM
        cursor.execute(
            'SELECT ComponentCode, Quantity FROM BOM WHERE Code = ?',
            (code,)
        )
        components = cursor.fetchall()

        for component_code, component_quantity in components:
            total_quantity = quantity * component_quantity
            cursor.execute(
                'INSERT INTO CommissionProgress (Commission, Code, QuantityRequired, QuantityPresent) VALUES (?, ?, ?, ?)',
                (inserted_id, component_code, total_quantity, 0)
            )

        db.commit()
        return redirect(url_for('view_commission'))

    date = request.args.get('date', '')
    code = request.args.get('code', '')
    quantity = request.args.get('quantity', '')

    return render_template('commission_add.html', date=date, code=code, quantity=quantity)


@app.route('/commission/delete/<id>')
def delete_commission(id):
    query_db('DELETE FROM Commission WHERE ID = ?', (id,))
    query_db('DELETE FROM CommissionProgress WHERE Commission = ?', (id,))
    return redirect(url_for('view_commission'))

@app.route('/commission/complete/<id>')
def complete_commission(id):
    query_db('UPDATE Commission SET Status = ? WHERE ID = ?', ("Complete", id))
    return redirect(url_for('view_commission'))


# CommissionProgress Routes
@app.route('/commissionprogress/<int:id>')
def view_commissionprogress(id):
    data = query_db('SELECT CommissionProgress.*, Item.* FROM CommissionProgress JOIN Item ON CommissionProgress.Code = Item.Code WHERE CommissionProgress.Commission = ?', (id,))
    return render_template('commissionprogress.html', data=data, current_date=date.today().isoformat(), id=id)


@app.route('/commissionprogress/increase/<int:id>')
def increase_commissionprogress(id):
    return_id = request.args.get('returnId', type=int)
    db = get_db()
    cursor = db.cursor()

    # Recupera il valore attuale di QuantityPresent
    cursor.execute('SELECT QuantityPresent, QuantityRequired FROM CommissionProgress WHERE ID = ?', (id,))
    row = cursor.fetchone()

    if row:
        quantity_present, quantity_required = row
        # Incrementa QuantityPresent solo se non supera il massimo richiesto
        if quantity_present < quantity_required:
            cursor.execute(
                'UPDATE CommissionProgress SET QuantityPresent = QuantityPresent + 1 WHERE ID = ?',
                (id,)
            )
            db.commit()

    return redirect(url_for('view_commissionprogress', id=return_id))


@app.route('/commissionprogress/decrease/<int:id>')
def decrease_commissionprogress(id):
    return_id = request.args.get('returnId', type=int)
    db = get_db()
    cursor = db.cursor()

    # Recupera il valore attuale di QuantityPresent
    cursor.execute('SELECT QuantityPresent FROM CommissionProgress WHERE ID = ?', (id,))
    row = cursor.fetchone()

    if row:
        quantity_present = row[0]
        # Decrementa QuantityPresent solo se è maggiore di 0
        if quantity_present > 0:
            cursor.execute(
                'UPDATE CommissionProgress SET QuantityPresent = QuantityPresent - 1 WHERE ID = ?',
                (id,)
            )
            db.commit()

    return redirect(url_for('view_commissionprogress', id=return_id))


# Item Routes
@app.route('/item')
def view_item():
    data = query_db('SELECT * FROM Item')
    return render_template('item.html', data=data)

@app.route('/item/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        query_db('INSERT INTO Item (Code, Type) VALUES (?, ?)',
                 (request.form['Code'], request.form['Type']))
        return redirect(url_for('view_item'))
    return render_template('item_add.html')

@app.route('/item/delete/<code>')
def delete_item(code):
    query_db('DELETE FROM Item WHERE Code = ?', (code,))
    return redirect(url_for('view_item'))


#  Stock Routes
@app.route('/stock')
def view_stock():
    data = query_db('SELECT * FROM Stock')
    return render_template('stock.html', data=data)

@app.route('/stock/increase/<itemCode>')
def increase_stock(itemCode):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE stock SET Quantity = Quantity + 1 WHERE ItemCode = ?', (itemCode,))
    db.commit()
    return redirect(url_for('view_stock'))


@app.route('/stock/decrease/<itemCode>')
def decrease_stock(itemCode):
    db = get_db()
    cursor = db.cursor()

    # Recupera il valore attuale di QuantityPresent
    cursor.execute('SELECT Quantity FROM stock WHERE ItemCode = ?', (itemCode,))
    row = cursor.fetchone()

    if row:
        quantity = row[0]
        if quantity > 0:
            cursor.execute(
                'UPDATE stock SET Quantity = Quantity - 1 WHERE ItemCode = ?',
                (itemCode,)
            )
            db.commit()

    return redirect(url_for('view_stock'))

# Variabili temporanee per l'ultimo codice e il suo conteggio (persi al refresh)
last_scanned = None
last_added_count = 0

@app.route('/stock/codereader', methods=['GET', 'POST'])
def codereader_stock():
    global last_scanned, last_added_count

    db = get_db()
    cursor = db.cursor()

    last_item = None  # Dati dell'ultimo item aggiornato

    if request.method == 'POST':
        raw_code = request.form.get('item_code', '').strip().upper()  # Case insensitive

        # Controlla se è un modificatore (MOD_Xn)
        mod_match = re.match(r"^MOD>X(\d+)$", raw_code)
        if mod_match:
            multiplier = int(mod_match.group(1))
            if last_scanned:
                last_added_count *= multiplier  # Moltiplica il conteggio precedente
            return render_template('stock_codereader.html', last_item=last_item, last_added_count=last_added_count)

        # Controlla se è un codice stock (IN>, OUT>, WORK>)
        match = re.match(r"^(IN|OUT|WORK)>(\w+)$", raw_code)
        if match:
            action, item_code = match.groups()

            # Se il nuovo codice è diverso dall'ultimo, resetta il contatore
            if last_scanned != item_code:
                last_added_count = 0

            last_scanned = item_code  # Memorizza l'ultimo codice
            last_added_count += 1  # Incrementa il contatore solo per l'ultimo inserito

            # Controlla se l'item esiste in stock
            cursor.execute("SELECT Quantity FROM Stock WHERE ItemCode = ?", (item_code,))
            row = cursor.fetchone()

            if action == "IN":
                if row:
                    cursor.execute("UPDATE Stock SET Quantity = Quantity + 1 WHERE ItemCode = ?", (item_code,))
                else:
                    cursor.execute("INSERT INTO Stock (ItemCode, Quantity) VALUES (?, 1)", (item_code,))

            elif action in ["OUT", "WORK"]:
                if row and row["Quantity"] > 0:
                    cursor.execute("UPDATE Stock SET Quantity = Quantity - 1 WHERE ItemCode = ?", (item_code,))

            db.commit()

            # Recupera l'ultimo elemento aggiornato
            cursor.execute("SELECT * FROM Stock WHERE ItemCode = ?", (item_code,))
            last_item = cursor.fetchone()

    return render_template('stock_codereader.html', last_item=last_item, last_added_count=last_added_count)


if __name__ == '__main__':
    app.run(debug=True)


# def recursiveProgressEntry(code):
    