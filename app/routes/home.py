# app/routes/home.py
from flask import Blueprint, render_template, jsonify
from app.utils import query_db

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():

    ordersOnGoing = query_db("""SELECT ProductionOrderProgress.*, Product.Category 
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status = "On Going"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted""")

    ordersPlanned = query_db("""SELECT ProductionOrderProgress.*, Product.Category, Product.Image 
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status = "Planned"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted""")


    return render_template("index.html", ordersOnGoing=ordersOnGoing, ordersPlanned=ordersPlanned)


@home_bp.route("/logs")
def logs():
    data = query_db('SELECT * FROM Logs ORDER BY timestamp DESC LIMIT 50')
    logs = [dict(row) for row in data]
    return jsonify(logs)
