# app/routes/metadata.py
import base64
from io import BytesIO
from PIL import Image
from flask import Blueprint, request, redirect, url_for, render_template
from app.utils import query_db

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.route('/Metadata')
def view_Metadata():
    data = query_db('SELECT * FROM Metadata')
    return render_template('Metadata.html', data=data)


@metadata_bp.route('/Metadata/add', methods=['GET', 'POST'])
def add_Metadata():
    if request.method == 'POST':
        try:
            metadata_code = request.form['MetadataCode']
            category = request.form['Category']

            # Inserisci nel DB
            query_db('INSERT INTO Metadata (MetadataCode, Category) VALUES (?, ?)',
                        (metadata_code, category))
            return redirect(url_for('metadata.view_Metadata'))
        except:
            return render_template('Metadata_add.html', message=f'The metadata {metadata_code} is already present in the database')

    return render_template('Metadata_add.html')


@metadata_bp.route('/Metadata/delete/<metadataCode>')
def delete_Metadata(metadataCode):
    query_db('DELETE FROM Metadata WHERE MetadataCode = ?', (metadataCode,))
    return redirect(url_for('metadata.view_Metadata'))
