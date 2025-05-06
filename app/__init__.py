# app/__init__.py
from flask import Flask, request, g
from app.utils import query_db
from app.routes import register_routes
from flask_login import LoginManager
from datetime import timedelta
from flask_login import current_user

login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # aggiorna col tuo blueprint effettivo

def create_app():
    app = Flask(__name__)
    app.permanent_session_lifetime = timedelta(days=30)
    app.config.from_object("config")

    login_manager.init_app(app)

    from app.models.user import User
    login_manager.user_loader(User.load_user)

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
    
    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            g.selected_user = current_user.id
        else:
            g.selected_user = "anonimo"


    return app