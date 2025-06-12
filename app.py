from flask import Flask, jsonify, abort
import json, requests

app = Flask(__name__)

with open('data.json', 'r', encoding='utf-8') as f:
    PRODUCTS = json.load(f)

# 1. get: /all_products/  - return all information about all products
@app.route('/all_products/', methods=['GET'])
def all_products():
    return jsonify(PRODUCTS)


# 2. get: /products/{product_name} - return information about exact product
@app.route('/products/<product_name>', methods=['GET'])
def get_product(product_name):
    product = PRODUCTS.get(product_name)
    return jsonify({product_name: product})


# 3. get: //products/{product_name}/{product_field} - return information about exact field  exact product
@app.route('/products/<product_name>/<product_field>', methods=['GET'])
def get_product_field(product_name, product_field):
    product = PRODUCTS.get(product_name)
    field_value = product.get(product_field)
    return jsonify({product_field: field_value})

if __name__ == '__main__':
    app.run(debug=True)