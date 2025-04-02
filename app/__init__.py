# app/__init__.py
from flask import Flask, request, g
from app.utils import query_db
from app.routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    register_routes(app)

    @app.before_request
    def load_selected_user():
        """Carica l'utente selezionato dal cookie e lo rende disponibile globalmente."""
        g.selected_user = request.cookies.get("selectedUser", "anonimo")

    @app.context_processor
    def inject_users():
        """Rende disponibile la lista utenti in tutti i template."""
        users = query_db("SELECT * FROM user")
        return {"users": users, "selected_user": g.selected_user}

    return app