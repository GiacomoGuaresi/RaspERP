# app/routes/progress.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.utils import query_db, get_db
from datetime import date

progress_bp = Blueprint("progress", __name__)

@progress_bp.route('/ProductionOrderProgress/<int:OrderID>')
def view_ProductionOrderProgress(OrderID):
    data = query_db("""
        SELECT ProductionOrderProgress.*, Product.*, 
               ProductionOrder.OrderID as childOrderId 
        FROM ProductionOrderProgress 
        JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode 
        LEFT JOIN ProductionOrder ON ProductionOrder.ParentOrderID = ProductionOrderProgress.OrderID 
        AND ProductionOrder.ProductCode = ProductionOrderProgress.ProductCode
        WHERE ProductionOrderProgress.OrderID = ?
    """, (OrderID,))
    
    order = query_db('SELECT * FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE OrderID = ?', (OrderID, ), one=True)
    
    return render_template('ProductionOrderProgress.html', data=data, current_date=date.today().isoformat(), order=order)

@progress_bp.route('/ProductionOrderProgress/increase/<int:ProgressID>')
def increase_ProductionOrderProgress(ProgressID):
    OrderID = request.args.get('OrderID', type=int)
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'SELECT QuantityCompleted, QuantityRequired FROM ProductionOrderProgress WHERE ProgressID = ?', 
        (ProgressID,))
    row = cursor.fetchone()

    if row:
        quantity_present, quantity_required = row
        if quantity_present < quantity_required:
            cursor.execute(
                'UPDATE ProductionOrderProgress SET QuantityCompleted = QuantityCompleted + 1 WHERE ProgressID = ?',
                (ProgressID,)
            )
            db.commit()

    return redirect(url_for('progress.view_ProductionOrderProgress', OrderID=OrderID))

@progress_bp.route('/ProductionOrderProgress/decrease/<int:ProgressID>')
def decrease_ProductionOrderProgress(ProgressID):
    OrderID = request.args.get('OrderID', type=int)
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'SELECT QuantityCompleted FROM ProductionOrderProgress WHERE ProgressID = ?', (ProgressID,))
    row = cursor.fetchone()

    if row and row["QuantityCompleted"] > 0:
        cursor.execute(
            'UPDATE ProductionOrderProgress SET QuantityCompleted = QuantityCompleted - 1 WHERE ProgressID = ?',
            (ProgressID,)
        )
        db.commit()

    return redirect(url_for('progress.view_ProductionOrderProgress', OrderID=OrderID))
