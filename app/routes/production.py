# app/routes/production.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.utils import query_db, get_db
from datetime import date

production_bp = Blueprint("production", __name__)

@production_bp.route('/ProductionOrder')
def view_ProductionOrder():
    data = query_db('SELECT * FROM ProductionOrder')
    return render_template('ProductionOrder.html', data=data)

@production_bp.route('/ProductionOrder/add', methods=['GET', 'POST'])
def add_ProductionOrder():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()

        orderDate = request.form['OrderDate']
        code = request.form['ProductCode']
        quantity = int(request.form['Quantity'])

        cursor.execute(
            'INSERT INTO ProductionOrder (OrderDate, ProductCode, Quantity) VALUES (?, ?, ?)',
            (orderDate, code, quantity)
        )
        inserted_id = cursor.lastrowid

        cursor.execute(
            'SELECT ChildProductCode, Quantity FROM BillOfMaterials WHERE ProductCode = ?',
            (code,)
        )
        components = cursor.fetchall()

        for component_code, component_quantity in components:
            total_quantity = quantity * component_quantity

            cursor.execute("SELECT * FROM Inventory WHERE ProductCode = ?", (component_code,))
            item = cursor.fetchone()

            used = min(total_quantity, (item[1] - item[2]) if item else 0)

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

        return redirect(url_for('production.view_ProductionOrder'))
    
    product_codes = query_db('SELECT ProductCode FROM Product')
    return render_template('ProductionOrder_add.html', OrderDate=date.today().isoformat(), product_codes=product_codes)

@production_bp.route('/ProductionOrder/delete/<OrderID>')
def delete_ProductionOrder(OrderID):
    query_db('DELETE FROM ProductionOrder WHERE OrderID = ?', (OrderID,))
    query_db('DELETE FROM ProductionOrderProgress WHERE OrderID = ?', (OrderID,))
    return redirect(url_for('production.view_ProductionOrder'))

@production_bp.route('/ProductionOrder/complete/<OrderID>')
def complete_ProductionOrder(OrderID):
    query_db('UPDATE ProductionOrder SET Status = ? WHERE OrderID = ?', ("Complete", OrderID))
    return redirect(url_for('production.view_ProductionOrder'))
