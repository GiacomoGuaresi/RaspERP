# app/routes/product.py
from flask import Blueprint, render_template, request, redirect, url_for
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
            query_db('INSERT INTO Product (ProductCode, Category) VALUES (?, ?)',
                    (request.form['ProductCode'], request.form['Category']))
            return redirect(url_for('product.view_Product'))
        except:
            return render_template('Product_add.html', message='The product ' + request.form['ProductCode'] + ' is already present in the database')
    return render_template('Product_add.html')

@product_bp.route('/Product/delete/<code>')
def delete_Product(code):
    query_db('DELETE FROM Product WHERE ProductCode = ?', (code,))
    return redirect(url_for('product.view_Product'))
