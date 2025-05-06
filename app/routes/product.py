# app/routes/product.py
import base64
from io import BytesIO
from PIL import Image
from flask import Blueprint, request, redirect, url_for, render_template
from app.utils import query_db
import json
from flask_login import login_required

product_bp = Blueprint("product", __name__)


@product_bp.route('/Product')
@login_required
def view_Product():
    data = query_db('SELECT * FROM Product')
    return render_template('Product.html', data=data)


@product_bp.route('/Product/<code>', methods=['GET'])
@login_required
def view_Product_detail(code):
    product = query_db(
        'SELECT * FROM Product WHERE ProductCode = ?', (code,), one=True)

    if not product:
        return render_template('error.html', message='Product not found'), 404

    return render_template('Product_view.html', product=product, metadata=json.loads(product['Metadata']))


@product_bp.route('/Product/add', methods=['GET', 'POST'])
@login_required
def add_Product():
    if request.method == 'POST':
        try:
            product_code = request.form['ProductCode']
            category = request.form['Category']
            image_file = request.files.get('ProductImage')

            image_base64 = None
            if image_file and image_file.filename != '':
                # Apri l'immagine e ridimensionala
                image = Image.open(image_file)
                # Mantiene le proporzioni con max 256px
                image.thumbnail((256, 256))

                # Converti in Base64
                buffered = BytesIO()
                # Usa JPEG per ridurre il peso
                image.save(buffered, format="JPEG")
                image_base64 = "data:image/png;base64, " + \
                    base64.b64encode(buffered.getvalue()).decode('utf-8')

            metaTemplate = query_db(
                "SELECT * FROM Metadata where Category = ?", (category,))
            metadata = {}
            for meta in metaTemplate:
                code = meta["MetadataCode"]
                metadata[code] = ""

            # Inserisci nel DB
            query_db('INSERT INTO Product (ProductCode, Category, Image, Metadata) VALUES (?, ?, ?, ?)',
                     (product_code, category, image_base64, json.dumps(metadata)))
            return redirect(url_for('product.view_Product'))
        except:
            return render_template('Product_add.html', message=f'The product {product_code} is already present in the database')

    return render_template('Product_add.html')


@product_bp.route('/Product/delete/<code>')
@login_required
def delete_Product(code):
    query_db('DELETE FROM Product WHERE ProductCode = ?', (code,))
    return redirect(url_for('product.view_Product'))


@product_bp.route('/Product/edit/<code>', methods=['GET', 'POST'])
@login_required
def edit_Product(code):
    product = query_db(
        'SELECT * FROM Product WHERE ProductCode = ?', (code,), one=True)

    if not product:
        return render_template('error.html', message='Product not found'), 404

    # Converti i metadati JSON in un dizionario Python
    product_metadata = json.loads(
        product['Metadata']) if product['Metadata'] else {}

    if request.method == 'POST':
        try:
            new_category = request.form['Category']
            image_file = request.files.get('ProductImage')

            # Mantieni l'immagine esistente se non ne viene caricata una nuova
            image_base64 = product['Image']
            if image_file and image_file.filename != '':
                image = Image.open(image_file)
                image.thumbnail((256, 256))
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                image_base64 = "data:image/png;base64, " + \
                    base64.b64encode(buffered.getvalue()).decode('utf-8')

            # Leggi i metadati aggiornati dal form
            metadata_keys = request.form.getlist('metadata_keys[]')
            metadata_values = request.form.getlist('metadata_values[]')
            new_metadata = dict(zip(metadata_keys, metadata_values))

            # Aggiorna il prodotto nel database
            query_db('UPDATE Product SET Category = ?, Image = ?, Metadata = ? WHERE ProductCode = ?',
                     (new_category, image_base64, json.dumps(new_metadata), code))

            return redirect(url_for('product.view_Product_detail', code=code))
        except:
            return render_template('Product_edit.html', message='Error updating product', product=product)

    return render_template('Product_edit.html', product=product, metadata=product_metadata)
