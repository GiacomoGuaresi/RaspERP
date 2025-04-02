# app/routes/home.py
from flask import Blueprint, render_template, jsonify, g
from app.utils import query_db
from collections import defaultdict

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():

    ordersOnGoing = query_db("""SELECT ProductionOrderProgress.*, Product.Category, ProductionOrder.ProductCode as OrderProductCode 
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status = "On Going"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted""")

    ordersPlanned = query_db("""SELECT ProductionOrderProgress.*, Product.Category, Product.Image, ProductionOrder.ProductCode as OrderProductCode 
    FROM ProductionOrderProgress
    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
    WHERE Status = "Planned"
    AND ProductionOrderProgress.QuantityRequired > ProductionOrderProgress.QuantityCompleted""")

    # Raggruppa ordersOnGoing per OrderProductCode
    grouped_orders_ongoing = defaultdict(list)
    for row in ordersOnGoing:
        grouped_orders_ongoing[row["OrderProductCode"]].append(row)

    # Raggruppa ordersPlanned per OrderProductCode
    grouped_orders_planned = defaultdict(list)
    for row in ordersPlanned:
        grouped_orders_planned[row["OrderProductCode"]].append(row)

    return render_template("index.html", grouped_orders_ongoing=grouped_orders_ongoing, grouped_orders_planned=grouped_orders_planned)


@home_bp.route("/logs")
def logs():
    data = query_db('SELECT * FROM Logs ORDER BY timestamp DESC LIMIT 50')
    logs = [dict(row) for row in data]
    return jsonify(logs)


@home_bp.route("/whoami")
def whoami():
    return jsonify({"selected_user": g.selected_user})