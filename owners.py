from flask import Blueprint, request, make_response, jsonify
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('owners', __name__, url_prefix='/owners')

@bp.route('/<owner_id>/boats', methods=['GET'])
def owner_get_public(owner_id):

    if request.method == "GET":

        query = client.query(kind=constants.boats)
        query.add_filter("public", "=", True)
        query.add_filter("owner", "=", owner_id)
        boat_list = list(query.fetch())

        # Check if boat exists
        if not boat_list:
            err = []
            res = make_response(json.dumps(err))
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 200
            return res

        for curr_boat in boat_list:
            curr_boat["id"] = curr_boat.key.id
            curr_boat["self"] = request.root_url + "boats/" + str(curr_boat.key.id)

        # Sends json response
        res = make_response(json.dumps(boat_list))
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 200
        return res


    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'GET')
        res.headers.set('Content-Type', 'text/html')
        res.status_code = 405
        return res