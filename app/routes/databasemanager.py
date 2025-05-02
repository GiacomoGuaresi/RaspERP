# app/routes/databasemanager.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file, flash
import sqlite3
from app.utils import query_db, log_action
import os
import shutil
import time

BASE_DIR = os.path.abspath(os.path.dirname(__file__) + "/../..")
DB_PATH = os.path.join(BASE_DIR, "database.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

databasemanager_bp = Blueprint("databasemanager", __name__)


@databasemanager_bp.route('/DatabaseManager', methods=['GET', 'POST'])
def view_DatabaseManager():
    tables = [row['name'] for row in query_db("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")]
    backups = sorted(os.listdir(BACKUP_DIR), reverse=True)

    if request.method == 'POST':
        query = request.form.get('query')
        try:
            if query.strip().lower().startswith("select"):
                result = query_db(query)
                print(result)
                columns = result[0].keys() if result else []
                return render_template('Databasemanager.html', result=result, columns=columns, tables=tables, backups=backups)
            else:
                query_db(query)
                return render_template('Databasemanager.html', message="Query eseguita con successo.", tables=tables, backups=backups)
        except sqlite3.Error as e:
            return render_template('Databasemanager.html', error=f"Errore SQL: {e}", tables=tables, backups=backups)
    return render_template('Databasemanager.html', tables=tables, backups=backups)

# Scarica DB
@databasemanager_bp.route('/download')
def download_db():
    return send_file(DB_PATH, as_attachment=True, download_name="database.db")

# Carica DB
@databasemanager_bp.route('/upload', methods=['POST'])
def upload_db():
    file = request.files.get('db_file')
    if file and file.filename.endswith('.db'):
        file.save(DB_PATH)
        flash("Database sostituito correttamente.", "success")
    else:
        flash("File non valido.", "danger")
    return redirect(url_for('databasemanager.view_DatabaseManager'))

# Backup DB
@databasemanager_bp.route('/backup', methods=['POST'])
def backup_db():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    flash(f"Backup creato: backup_{timestamp}.db", "success")
    return redirect(url_for('databasemanager.view_DatabaseManager'))

# Ripristina da backup
@databasemanager_bp.route('/restore', methods=['POST'])
def restore_backup():
    filename = request.form.get('backup_file')
    if filename and filename.endswith(".db"):
        backup_path = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DB_PATH)
            flash(f"Backup {filename} ripristinato.", "success")
        else:
            flash("Backup non trovato.", "danger")
    return redirect(url_for('databasemanager.view_DatabaseManager'))