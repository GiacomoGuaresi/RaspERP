# app/utils.py
from app.database import get_db

def query_db(query, args=(), one=False):
    with get_db() as db:
        cur = db.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        db.commit()
    return (rv[0] if rv else None) if one else rv

def log_action(cursor, message, user):
    cursor.execute("INSERT INTO logs (message, user) VALUES (?, ?)", (message, user))
