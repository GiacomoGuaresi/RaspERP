# app/routes/production.py
from flask import Blueprint, render_template, request, redirect, url_for, g
from app.utils import query_db, get_db, get_current_user, log_action
from app.routes.inventory import increase_Inventory
from datetime import date
import json
from flask_login import login_required


production_bp = Blueprint("production", __name__)


@production_bp.route('/ProductionOrder')
@login_required
def view_ProductionOrder():
    if get_current_user() is not None and get_current_user() != "":
        data = query_db('SELECT * FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE (AssignedUser = ? OR AssignedUser = "")', (get_current_user(),))
    else:
        data = query_db(
            'SELECT * FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode')
    return render_template('ProductionOrder.html', data=data)


@production_bp.route('/ProductionOrder/add', methods=['GET', 'POST'])
@login_required
def add_ProductionOrder():
    if request.method == 'POST':
        orderDate = request.form['OrderDate']
        code = request.form['ProductCode']
        quantity = int(request.form['Quantity'])
        parentOrderID = request.form['ParentOrderID']
        assignedUser = request.form['AssignedUser']
        status = request.form['Status']
        add_ProductionOrder_process(
            orderDate, code, quantity, parentOrderID, assignedUser, status)
        return redirect(url_for('production.view_ProductionOrder'))

    orderDate = request.args.get('date', date.today().isoformat())
    code = request.args.get('code', '')
    quantity = request.args.get('quantity', '')
    parentOrderID = request.args.get('parentOrderID', '')
    status = request.args.get("status", 'Planned')

    product_codes = query_db('SELECT ProductCode FROM Product')

    return render_template('ProductionOrder_add.html', OrderDate=orderDate, ProductCode=code, Quantity=quantity, product_codes=product_codes, ParentOrderID=parentOrderID, status=status)


@production_bp.route('/ProductionOrder/delete/<OrderID>')
@login_required
def delete_ProductionOrder(OrderID):
    def delete_ProductionOrder_recursive(OrderID):
        data = query_db(
            """select * from ProductionOrder  where ParentOrderID = ?""", (OrderID,))
        for row in data:
            delete_ProductionOrder_recursive(row["OrderID"])

        query_db('DELETE FROM ProductionOrder WHERE OrderID = ?', (OrderID,))
        query_db('DELETE FROM ProductionOrderProgress WHERE OrderID = ?', (OrderID,))

    delete_ProductionOrder_recursive(OrderID)
    return redirect(url_for('production.view_ProductionOrder'))


@production_bp.route('/ProductionOrder/complete/<OrderID>')
@login_required
def complete_ProductionOrder(OrderID):
    query_db('UPDATE ProductionOrder SET Status = ? WHERE OrderID = ?',
             ("Complete", OrderID))
    
    quantity = query_db('SELECT Quantity FROM ProductionOrder WHERE OrderID = ?', (OrderID,))[0]["Quantity"]
    productCode = query_db('SELECT ProductCode FROM ProductionOrder WHERE OrderID = ?', (OrderID,))[0]["ProductCode"]
    # call increase_Inventory(ProductCode) 
    for i in range(quantity):
        increase_Inventory(productCode)

    return redirect(url_for('production.view_ProductionOrder'))


@production_bp.route('/ProductionOrder/ongoing/<OrderID>')
@login_required
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
        total_quantity = progress["QuantityRequired"] - \
            progress["QuantityCompleted"]
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
@login_required
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
@login_required
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


@production_bp.route('/ProductionOrder/addAllSub/<OrderID>')
@login_required
def addAllSub_ProductionOrder(OrderID):
    baseOrderInfo = query_db(
        """select * from ProductionOrder where OrderID = ?""", (OrderID,))
    orderDate = baseOrderInfo[0]["OrderDate"]
    status = baseOrderInfo[0]["Status"]

    def addAllSub_ProductionOrder_recursive(OrderID, orderDate, status):
        data = query_db("""SELECT *
            FROM ProductionOrderProgress
            JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
            LEFT JOIN ProductionOrder ON ProductionOrder.ParentOrderID = ProductionOrderProgress.OrderID AND ProductionOrder.ProductCode = ProductionOrderProgress.ProductCode
            WHERE ProductionOrderProgress.OrderID = ? AND Category = "Subassembly" and ProductionOrder.OrderID IS null""", (OrderID,))
        for row in data:
            metadata = json.loads(row["Metadata"])

            code = row["ProductCode"]
            quantity = row["QuantityRequired"] - row["QuantityCompleted"]
            parentOrderID = OrderID
            assignedUser = metadata.get("DefaultUser", "")

            log_action("Create Suborder for " + code)
            print("Create Suborder for " + code)
            inserted_id = add_ProductionOrder_process(
                orderDate, code, quantity, parentOrderID, assignedUser, status)
            
            if(status == "On Going"):
                ongoing_ProductionOrder(inserted_id)

            addAllSub_ProductionOrder_recursive(inserted_id, orderDate, status)

    addAllSub_ProductionOrder_recursive(OrderID, orderDate, status)

    return redirect(url_for('progress.view_ProductionOrderProgress', OrderID=OrderID))


def add_ProductionOrder_process(orderDate, code, quantity, parentOrderID, assignedUser, status):
    db = get_db()
    cursor = db.cursor()

    # Inserisce la ProductionOrder principale
    cursor.execute(
        'INSERT INTO ProductionOrder (OrderDate, ProductCode, Quantity, ParentOrderID, AssignedUser, Status) VALUES (?, ?, ?, ?, ?, ?)',
        (orderDate, code, quantity, parentOrderID, assignedUser, status)
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

    return inserted_id
