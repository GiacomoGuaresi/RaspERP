# app/routes/bom.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.utils import query_db, log_action


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
    query_db('DELETE FROM BillOfMaterials WHERE BillOfMaterialID = ?',
             (ProductCode,))
    return redirect(url_for('bom.view_BillOfMaterials'))


@bom_bp.route("/BillOfMaterials/graphs/")
def graphs_BillOfMaterials():
    data = query_db('SELECT ProductCode FROM Product WHERE Category IS "Product"')
    return render_template('BillOfMaterials_graphs.html', data=data)


@bom_bp.route("/BillOfMaterials/graphs/<product_code>")
def get_bom(product_code):
    return jsonify(get_bom_tree(product_code))


def get_bom_tree(product_code):
    rows = query_db("""
    WITH RECURSIVE bom_tree AS (
        SELECT ProductCode, ChildProductCode, Quantity
        FROM BillOfMaterials
        WHERE ProductCode = ?
        UNION ALL
        SELECT b.ProductCode, b.ChildProductCode, b.Quantity
        FROM BillOfMaterials b
        INNER JOIN bom_tree bt ON b.ProductCode = bt.ChildProductCode
    )
    SELECT * FROM bom_tree;
    """, (product_code,))

    tree = []
    for row in rows:
        tree.append({
            "product": row[0],
            "child": row[1],
            "quantity": row[2]
        })

    return tree
