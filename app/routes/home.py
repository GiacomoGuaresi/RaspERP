# app/routes/home.py
from flask import Blueprint, render_template, jsonify
from app.utils import query_db

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    return render_template("index.html")


@home_bp.route("/logs")
def logs():
    data = query_db('SELECT * FROM Logs ORDER BY timestamp DESC LIMIT 50')
    logs = [dict(row) for row in data]
    return jsonify(logs)
