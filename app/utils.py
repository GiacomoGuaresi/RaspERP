# app/utils.py
from app.database import get_db
from flask import g
import html
from urllib.parse import unquote

def query_db(query, args=(), one=False):
    with get_db() as db:
        cursor = db.cursor()
        
        # Costruire la query con i valori interpolati (non eseguita ancora)
        full_query = query.replace("?", "{}").format(*map(repr, args))
        print(full_query)  # Stampa per debug

        cursor.execute(query, args)
        rv = cursor.fetchall()
        db.commit()
        
        # Loggare la query se non è una SELECT
        if not query.strip().upper().startswith("SELECT"):
            log_action(full_query)

    return (rv[0] if rv else None) if one else rv

def log_action(message):
    with get_db() as db:
        cursor = db.cursor()
        """Registra un'azione nei log associandola all'utente selezionato automaticamente."""
        cursor.execute("INSERT INTO logs (message, user) VALUES (?, ?)", (message, get_current_user()))


def get_current_user():
    return unquote(g.get("selected_user", "anonimo"))