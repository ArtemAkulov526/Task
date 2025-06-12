from flask import Flask, jsonify, abort
import json

app = Flask(__name__)

with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)


# 1. get: /all_products/  - return all information about all products
@app.route('/all_products/', methods=['GET'])
def all_products():
    return jsonify(data)

# 2. get: /products/{product_name} - return information about exact product
@app.route('/products/<product_name>', methods=['GET'])
def get_product(product_name):
    product = data.get(product_name)
    if not product:
        abort(404, description=f"Product '{product_name}' not found.")
    return jsonify({product_name: product})


# 3. get: /products/{product_name}/{product_field} - return information about exact field  exact product
@app.route('/products/<product_name>/<product_field>', methods=['GET'])
def get_product_field(product_name, product_field):
    product = data.get(product_name)
    if not product:
        abort(404, description=f"Product '{product_name}' not found.")
    if product_field in product:
        return jsonify({product_field: product[product_field]})
    nutrition = product.get({})
    if product_field in nutrition:
        return jsonify({product_field: nutrition[product_field]})

    abort(404, description=f"Field '{product_field}' not found for product '{product_name}'.")

if __name__ == '__main__':
    app.run(debug=True)