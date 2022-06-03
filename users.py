from flask import Blueprint, request, make_response, jsonify
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('', methods=['GET'])
def user_get_public():

    if 'application/json' not in request.accept_mimetypes:
        # Checks if client accepts json, if not return 406
        err = {"Error": "The request header ‘Accept' is not application/json"}
        res = make_response(err)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 406
        return res

    if request.method == "GET":
        query = client.query(kind=constants.users)
        results = list(query.fetch())
        user_list = {"self": request.root_url + "users", "users": results}

        # Sends json response
        res = make_response(json.dumps(user_list))
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 200
        return res

    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'GET')
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 405
        return res
