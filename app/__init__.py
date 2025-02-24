# app/__init__.py
from flask import Flask
from app.database import get_db
from app.routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    register_routes(app)

    return app
