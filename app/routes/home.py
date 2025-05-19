# app/routes/home.py
from flask import Blueprint, render_template, jsonify, g, request
from app.utils import query_db, get_current_user
from collections import defaultdict
from flask_login import login_required

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
@login_required
def index():
    # Product ProductionOrder count
    data = {}
    if get_current_user() is not None and get_current_user() != "":
        data = query_db('SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE Status = "On Going" AND Category="Product" AND (AssignedUser = ? OR AssignedUser = "")', (get_current_user(),))
    else:
        data = query_db(
            'SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE Status = "On Going" AND Category="Product"')
    productProductionOrder = data[0]["productionOrderNumber"]

    # Subassembly ProductionOrder count
    data = {}
    if get_current_user() is not None and get_current_user() != "":
        data = query_db('SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE Status = "On Going" AND Category="Subassembly" AND (AssignedUser = ? OR AssignedUser = "")', (get_current_user(),))
    else:
        data = query_db(
            'SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE Status = "On Going" AND Category="Subassembly"')
    subassemblyProductionOrder = data[0]["productionOrderNumber"]

    def get_missing_parts_by_category(category):
        try:
            result = {}
            if get_current_user() is not None and get_current_user() != "":
                result = query_db(f"""
                    SELECT SUM(ProductionOrderProgress.QuantityRequired) - SUM(ProductionOrderProgress.QuantityCompleted) as MissingParts
                    FROM ProductionOrderProgress
                    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
                    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
                    WHERE ProductionOrder.Status = "On Going"
                    AND (AssignedUser = ? OR AssignedUser = "")
                    AND Product.Category = ?""", (get_current_user(), category,))
            else:
                result = query_db(f"""
                    SELECT SUM(ProductionOrderProgress.QuantityRequired) - SUM(ProductionOrderProgress.QuantityCompleted) as MissingParts
                    FROM ProductionOrderProgress
                    JOIN ProductionOrder ON ProductionOrderProgress.OrderID = ProductionOrder.OrderID
                    JOIN Product ON ProductionOrderProgress.ProductCode = Product.ProductCode
                    WHERE ProductionOrder.Status = "On Going"
                    AND Product.Category = ?""", (category, ))
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

    return render_template("index.html", productProductionOrder=productProductionOrder, subassemblyProductionOrder=subassemblyProductionOrder, missingPartsPrintedPart=missingPartsPrintedPart, missingPartsComponent=missingPartsComponent, missingPartsSubassembly=missingPartsSubassembly)


@home_bp.route("/logs")
@login_required
def logs():
    data = query_db('SELECT * FROM Logs ORDER BY timestamp DESC LIMIT 50')
    logs = [dict(row) for row in data]
    return jsonify(logs)


@home_bp.route("/whoami")
@login_required
def whoami():
    returnObject = {}
    
    ip = request.remote_addr
    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("127."):
        returnObject["Side"] = "Internal"
        returnObject["ip"] = ip
    else:
        returnObject["Side"] = "External"
        returnObject["ip"] = ip
    
    returnObject["user"] = get_current_user()

    return jsonify(returnObject)


