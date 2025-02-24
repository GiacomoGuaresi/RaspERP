# app/routes/bom.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.utils import query_db

bom_bp = Blueprint("bom", __name__)

@bom_bp.route('/BillOfMaterials')
def view_BillOfMaterials():
    data = query_db('SELECT * FROM BillOfMaterials')
    return render_template('BillOfMaterials.html', data=data)

@bom_bp.route('/BillOfMaterials/add', methods=['GET', 'POST'])
def add_BillOfMaterials():
    if request.method == 'POST':
        query_db('INSERT INTO BillOfMaterials (ProductCode, ChildProductCode, Quantity) VALUES (?, ?, ?)',
                 (request.form['ProductCode'], request.form['ChildProductCode'], int(request.form['Quantity'])))
        return redirect(url_for('bom.view_BillOfMaterials'))

    product_codes = query_db('SELECT ProductCode FROM Product')
    return render_template('BillOfMaterials_add.html', product_codes=product_codes)

@bom_bp.route('/BillOfMaterials/delete/<ProductCode>')
def delete_BillOfMaterials(ProductCode):
    query_db('DELETE FROM BillOfMaterials WHERE BillOfMaterialID = ?', (ProductCode,))
    return redirect(url_for('bom.view_BillOfMaterials'))
