# app/routes/product.py
import base64
from io import BytesIO
from PIL import Image
from flask import Blueprint, request, redirect, url_for, render_template
from app.utils import query_db

product_bp = Blueprint("product", __name__)

@product_bp.route('/Product')
def view_Product():
    data = query_db('SELECT * FROM Product')
    return render_template('Product.html', data=data)

@product_bp.route('/Product/add', methods=['GET', 'POST'])
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
                image.thumbnail((256, 256))  # Mantiene le proporzioni con max 256px

                # Converti in Base64
                buffered = BytesIO()
                image.save(buffered, format="JPEG")  # Usa JPEG per ridurre il peso
                image_base64 = "data:image/png;base64, " + base64.b64encode(buffered.getvalue()).decode('utf-8')

            # Inserisci nel DB
            query_db('INSERT INTO Product (ProductCode, Category, Image) VALUES (?, ?, ?)',
                     (product_code, category, image_base64))
            return redirect(url_for('product.view_Product'))
        except:
            return render_template('Product_add.html', message=f'The product {product_code} is already present in the database')

    return render_template('Product_add.html')

@product_bp.route('/Product/delete/<code>')
def delete_Product(code):
    query_db('DELETE FROM Product WHERE ProductCode = ?', (code,))
    return redirect(url_for('product.view_Product'))
