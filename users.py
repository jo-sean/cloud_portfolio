from flask import Blueprint, request, make_response, jsonify
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('', methods=['GET'])
def user_get_public():

    if not request.is_json:
        # Checks if sent data is json, if not return 415
        err = {"Error": "The request header 'content_type' is not application/json "
                        "and/or the sent request body does not contain json"}
        res = make_response(err)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 415
        return res

    elif 'application/json' not in request.accept_mimetypes:
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
