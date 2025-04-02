# app/routes/home.py
from flask import Blueprint, render_template, jsonify, g
from app.utils import query_db, get_current_user
from collections import defaultdict

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    data = {}

    if get_current_user() is not None and get_current_user() != "":
        data = query_db('SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode WHERE AssignedUser = ?', (get_current_user(),))
    else:
        data = query_db('SELECT count(1) as productionOrderNumber FROM ProductionOrder LEFT JOIN Product ON Product.ProductCode = ProductionOrder.ProductCode')
    
    productionOrder = data[0]["productionOrderNumber"]

    return render_template("index.html", productionOrder=productionOrder)


@home_bp.route("/logs")
def logs():
    data = query_db('SELECT * FROM Logs ORDER BY timestamp DESC LIMIT 50')
    logs = [dict(row) for row in data]
    return jsonify(logs)


@home_bp.route("/whoami")
def whoami():
    return jsonify({"selected_user": g.selected_user})