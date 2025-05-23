# app/routes/progress.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.utils import query_db, get_db
from datetime import date
from flask_login import login_required

progress_bp = Blueprint("progress", __name__)

@progress_bp.route('/ProductionOrderProgress/<int:OrderID>')
@login_required
def view_ProductionOrderProgress(OrderID):
    data = query_db("""
        SELECT ProductionOrderProgress.*, Product.*, 
               ProductionOrder.OrderID as childOrderId, ProductionOrder.AssignedUser, ProductionOrder.Status
        FROM ProductionOrderProgress 
        JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode 
        LEFT JOIN ProductionOrder ON ProductionOrder.ParentOrderID = ProductionOrderProgress.OrderID 
        AND ProductionOrder.ProductCode = ProductionOrderProgress.ProductCode
        WHERE ProductionOrderProgress.OrderID = ?
    """, (OrderID,))
    
    order = query_db('SELECT * FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE OrderID = ?', (OrderID, ), one=True)
    
    return render_template('ProductionOrderProgress.html', data=data, current_date=date.today().isoformat(), order=order)