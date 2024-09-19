from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from models import *
from sqlalchemy import and_

# create the app
app = Flask(__name__)
db_name = 'catalog.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# initialize the app with Flask-SQLAlchemy
db.init_app(app)

with app.app_context():
    db.create_all()

def serialize(prod):
    p_array = []
    for p in prod:
        rt = {
            "name": p.name, 
            "description": p.description, 
            "price": p.price, 
            "inventory_count": p.count, 
            "category": p.category,
            "popularity": p.popularity
        }
        p_array.append(rt)
    return p_array

@app.route('/')
def testdb():
    try:
        db.session.query(text('1')).from_statement(text('SELECT 1')).all()
        return '<h1>It works.</h1>'
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text

# CREATE A PRODUCT 
# API INPUT : COLUMNS OF PRODUCT TABLE EXCEPT POPULARITY WHICH IS DYNAMICALLY CALCULATED
# API OUTPUT : ON SUCCESSFUL CREATION RETURNS PRODUCT ID, ELSE 404
    
@app.route('/product/create', methods=['POST'])
def create_product():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    count = data.get('count')
    price = data.get('price')
    category = data.get('category')
    product = Product(
        name = name,
        description = description,
        count = count,
        price = price,
        category = category,
        popularity = 0.0
    )
    db.session.add(product)
    db.session.commit()
    
    return jsonify({"id": product.id}), 200

# GET A PRODUCT 
# API INPUT : PRODUCT ID
# API OUTPUT : IF FOUND RETURNS PRODUCT DETAILS, ELSE 404

@app.route('/product/<id>', methods=['GET'])
def get_product(id):
    prod = db.session.execute(db.select(Product)
          .filter_by(id=id)).scalars()
    if prod:
        prod = serialize(prod)
        return jsonify(prod), 200
    else:
        return jsonify({"error": "Product not found"}), 404

# EDIT A PRODUCT 
# API INPUT : FIELDS OF PRODUCT TABLE EXCEPT POPULARITY WHICH IS DYNAMICALLY CALCULATED
# API OUTPUT : ON SUCCESSFUL UPDATE RETURNS PRODUCT ID, ELSE 404
    
@app.route('/product/edit', methods=['POST'])
def edit_product():
    data = request.json
    id = data.get('id')
    product = Product.query.get_or_404(id)
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = data['price']
    if 'inventory_count' in data:
        product.inventory_count = data['inventory_count']
    if 'category' in data:
        product.category = data['category']
    
    db.session.commit()
    
    return jsonify({"id": product.id}), 200

# DELETE A PRODUCT 
# API INPUT : PRODUCT ID
# API OUTPUT : ON SUCCESSFUL DELETION RETURNS CUSTOM MESSAGE, ELSE 404

@app.route('/product/delete/<id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return {'message': 'Product deleted successfully'}, 200

# FILTER PRODUCTS BASED ON NAME, DESCRIPTION, CATEGORY 
# API INPUT : NAME, DESCRIPTION, CATEGORY 
# API OUTPUT : IF FOUND RETURNS PRODUCTS' DETAILS, ELSE EMPTY ARRAY []

@app.route('/product/filter', methods=['POST'])
def filter_product():
    data = request.json
    query = db.select(Product)
    conditions = []
    if 'description' in data:
        description = data.get('description')
        conditions.append(Product.description == description)
    if 'name' in data:
        name = data.get('name')
        conditions.append(Product.name == name)
    if 'category' in data:
        category = data.get('category')
        conditions.append(Product.category == category)
    
    if conditions:
        query = query.filter(and_(*conditions))

    return jsonify(serialize(db.session.execute(query).scalars().all())), 200

# UPDATE INVENTORY & POPULARITY IN CASE OF PRODUCT SALE 
# API INPUT : PRODUCT ID AND UNITS SOLD 
# API OUTPUT : IF FOUND RETURNS PRODUCT ID, ELSE 404

@app.route('/product/sale', methods=['POST'])
def sale_product():
    data = request.json
    order = data.get('order')
    id = data.get('id')
    product = Product.query.get_or_404(id)
    
    product.popularity = order*0.1 #Arbitary value to calculate popularity based on number of units sold
    product.count -= order
    
    db.session.commit()
    
    return jsonify({"id": product.id}), 200

if __name__ == '__main__':
    app.run(debug=True)