# app/routes/home.py
from flask import Blueprint, render_template, jsonify, g
from app.utils import query_db, get_current_user
from collections import defaultdict

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    # ProductionOrder count
    data = {}
    if get_current_user() is not None and get_current_user() != "":
        data = query_db('SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE AssignedUser = ?', (get_current_user(),))
    else:
        data = query_db(
            'SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode')
    productionOrder = data[0]["productionOrderNumber"]
    def get_missing_parts_by_category(category):
        try:
            result = query_db(f"""
                SELECT SUM(ProductionOrderProgress.QuantityRequired) - SUM(ProductionOrderProgress.QuantityCompleted) as MissingParts
                FROM ProductionOrderProgress
                JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
                JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
                WHERE ProductionOrder.Status = "On Going"
                AND Product.Category = "{category}"
            """)
            if result and result[0] and result[0]["MissingParts"] is not None:
                return result[0]["MissingParts"]
            else:
                return 0
        except IndexError:
            return 0

    # MissingParts / PrintedParts
    missingPartsPrintedPart = get_missing_parts_by_category("PrintedPart")
    print(missingPartsPrintedPart)

    # MissingParts / Component
    missingPartsComponent = get_missing_parts_by_category("Component")
    print(missingPartsComponent)

    # MissingParts / Subassembly
    missingPartsSubassembly = get_missing_parts_by_category("Subassembly")
    print(missingPartsSubassembly)

    return render_template("index.html", productionOrder=productionOrder, missingPartsPrintedPart=missingPartsPrintedPart, missingPartsComponent=missingPartsComponent, missingPartsSubassembly=missingPartsSubassembly)


@home_bp.route("/logs")
def logs():
    data = query_db('SELECT * FROM Logs ORDER BY timestamp DESC LIMIT 50')
    logs = [dict(row) for row in data]
    return jsonify(logs)


@home_bp.route("/whoami")
def whoami():
    return jsonify({"selected_user": g.selected_user})
