# app/routes/production.py
from flask import Blueprint, render_template, request, redirect, url_for, g
from app.utils import query_db, get_db, get_current_user
from datetime import date

production_bp = Blueprint("production", __name__)


@production_bp.route('/ProductionOrder')
def view_ProductionOrder():
    if get_current_user() is not None and get_current_user() != "":
        data = query_db('SELECT * FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE AssignedUser = ?', (get_current_user(),))
    else:
        data = query_db('SELECT * FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode')
    return render_template('ProductionOrder.html', data=data)


@production_bp.route('/ProductionOrder/add', methods=['GET', 'POST'])
def add_ProductionOrder():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()

        orderDate = request.form['OrderDate']
        code = request.form['ProductCode']
        quantity = int(request.form['Quantity'])
        parentOrderID = request.form['ParentOrderID']
        assignedUser = request.form['AssignedUser']

        # Inserisce la ProductionOrder principale
        cursor.execute(
            'INSERT INTO ProductionOrder (OrderDate, ProductCode, Quantity, ParentOrderID, AssignedUser) VALUES (?, ?, ?, ?, ?)',
            (orderDate, code, quantity, parentOrderID, assignedUser)
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
                'INSERT INTO ProductionOrderProgress (OrderID, ProductCode, QuantityRequired, QuantityCompleted) VALUES (?, ?, ?, 0)',
                (inserted_id, component_code, total_quantity,)
            )

            db.commit()

        db.commit()
        return redirect(url_for('production.view_ProductionOrder'))

    orderDate = request.args.get('date', date.today().isoformat())
    code = request.args.get('code', '')
    quantity = request.args.get('quantity', '')
    parentOrderID = request.args.get('parentOrderID', '')

    product_codes = query_db('SELECT ProductCode FROM Product')

    return render_template('ProductionOrder_add.html', OrderDate=orderDate, ProductCode=code, Quantity=quantity, product_codes=product_codes, ParentOrderID=parentOrderID)


@production_bp.route('/ProductionOrder/delete/<OrderID>')
def delete_ProductionOrder(OrderID):
    query_db('DELETE FROM ProductionOrder WHERE OrderID = ?', (OrderID,))
    query_db('DELETE FROM ProductionOrderProgress WHERE OrderID = ?', (OrderID,))
    return redirect(url_for('production.view_ProductionOrder'))


@production_bp.route('/ProductionOrder/complete/<OrderID>')
def complete_ProductionOrder(OrderID):
    query_db('UPDATE ProductionOrder SET Status = ? WHERE OrderID = ?',
             ("Complete", OrderID))
    return redirect(url_for('production.view_ProductionOrder'))


@production_bp.route('/ProductionOrder/ongoing/<OrderID>')
def ongoing_ProductionOrder(OrderID):
    db = get_db()
    cursor = db.cursor()
    query_db('UPDATE ProductionOrder SET Status = ? WHERE OrderID = ?',
             ("On Going", OrderID))

    # Cerca i componenti nei progress
    cursor.execute(
        'SELECT * FROM ProductionOrderProgress WHERE OrderID = ?', (OrderID,))
    all_progress = cursor.fetchall()

    for progress in all_progress:
        total_quantity = progress["QuantityRequired"] - progress["QuantityCompleted"]
        productCode = progress["ProductCode"]
        progressID = progress["ProgressID"]
        cursor.execute(
            "SELECT * FROM Inventory WHERE ProductCode = ?", (productCode,))
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
            'UPDATE ProductionOrderProgress SET QuantityCompleted = QuantityCompleted + ? WHERE ProgressID = ?',
            (used, progressID)
        )

        if used > 0:
            cursor.execute(
                'UPDATE Inventory SET Locked = Locked + ? WHERE ProductCode = ?',
                (used, productCode,)
            )

        db.commit()

    return redirect(url_for('production.view_ProductionOrder'))

@production_bp.route('/ProductionOrder/increase/<int:OrderID>')
def increase_ProductionOrder(OrderID):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'SELECT QuantityCompleted, Quantity FROM ProductionOrder WHERE OrderID = ?', 
        (OrderID,))
    row = cursor.fetchone()

    if row:
        quantity_present, quantity_required = row
        if quantity_present < quantity_required:
            cursor.execute(
                'UPDATE ProductionOrder SET QuantityCompleted = QuantityCompleted + 1 WHERE OrderID = ?',
                (OrderID,)
            )
            db.commit()

    return redirect(url_for('progress.view_ProductionOrderProgress', OrderID=OrderID))



@production_bp.route('/ProductionOrder/decrease/<int:OrderID>')
def decrease_ProductionOrder(OrderID):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'SELECT QuantityCompleted FROM ProductionOrder WHERE OrderID = ?', (OrderID,))
    row = cursor.fetchone()

    if row and row["QuantityCompleted"] > 0:
        cursor.execute(
            'UPDATE ProductionOrder SET QuantityCompleted = QuantityCompleted - 1 WHERE OrderID = ?',
            (OrderID,)
        )
        db.commit()

    return redirect(url_for('progress.view_ProductionOrderProgress', OrderID=OrderID))

