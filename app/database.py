# app/database.py
import sqlite3
from flask import g

DB_NAME = 'database.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()
