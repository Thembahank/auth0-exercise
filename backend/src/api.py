import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# set response headers
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Headers", "Content-Type , Authorization, Data-Type", )
    response.headers.add("Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, PATCH, OPTIONS")
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

@app.route('/drinks', methods=['GET'])
def public_retrieve_drinks():
    """return all available categories"""

    if request.method == 'GET':
        try:
            drinks = Drink.query.all()

            return jsonify({
                'success': True,
                'drinks': [drink.short() for drink in drinks]
            }),200

        except:
            abort(404)


@app.route('/drinks-detail', methods=['GET'])
@requires_auth(permission='get:drinks-detail')
def retrieve_drinks(jwt):
    """return all available categories"""

    if request.method == 'GET':
        try:
            drinks = Drink.query.all()

            return jsonify({
                'success': True,
                'drinks': [drink.long() for drink in drinks]
            }), 200

        except:
            abort(422)


@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def add_drinks(jwt):
    """
    POST: creates new drink
    """

    if request.method == 'POST':

        body = request.get_json()
        title = body.get('title', None)
        recipe = json.dumps(body.get('recipe', None))
        print(body,title,recipe)

        try:

            # reject if any of the fields are missing
            if title is None or recipe is None:
                abort(422)

            # create a new drink
            drink_obj = Drink(title=title, recipe=str(recipe))
            drink_obj.insert()

            drinks = Drink.query.filter(Drink.id==drink_obj.id).one_or_none()
            return jsonify({
                'success': True,
                'drinks': [drink_obj.long()],
            }),200

        except Exception as e:
            print(e)
            abort(422)


@app.route('/drinks/<drink_id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drink(jwt,drink_id):
    if request.method == 'PATCH':
        try:
            print('patching')
            drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
            print(drink_id)

            body = request.get_json()
            title = body.get('title', None)
            recipe = body.get('recipe', None)

            print(recipe,title)

            # if not found reject
            if drink is None:
                abort(404)

            if recipe is not None:
                drink.recipe = json.dumps(recipe)

            if title is not None:
                drink.title = title

            drink.update()
            print(drink.long())

            return jsonify({
                'success': True,
                'drinks': [drink.long()],
            })

        except Exception as e:
            print(e)
            abort(422)


@app.route('/drinks/<drink_id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drinks(jwt,drink_id):
    if request.method == 'DELETE':
        try:
            drink = Drink.query.filter(Drink.id == int(drink_id)).one_or_none()

            if drink is None:
                abort(404)

            drink.delete()

            return jsonify({
                'success': True,
                'delete': drink_id,
            }),200

        except Exception as e:
            print(e)
            abort(422)


## Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found",
    }), 404

@app.errorhandler(403)
def permission_not_found(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Permission not found",
    }), 403


@app.errorhandler(AuthError)
def not_found(error):
    return jsonify({
        "success": False,
        "error": error.error['code'],
        "message": error.error['description'],
    }), error.status_code
