from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
from google.oauth2 import id_token
from google.auth.transport import requests
import constants

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')


@bp.route('', methods=['POST', 'GET'])
def loads_get_post():
    if request.method == 'POST':
        content = request.get_json()

        # Check contents of the json file to make sure keys have values, and it is not empty
        if not content or "volume" not in content or "item" not in content or "creation_date" not in content:
            return {"Error": "The request object is missing at least one of the required attributes"}, 400

        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        new_load.update({"volume": content["volume"], "carrier": None, "item": content["item"],
                         "creation_date": content["creation_date"]})
        client.put(new_load)

        new_load["id"] = new_load.key.id
        new_load["self"] = request.base_url + "/" + str(new_load.key.id)

        return json.dumps(new_load), 201

    elif request.method == 'GET':
        # Get query of loads and set the limit and offset for the query

        query = client.query(kind=constants.loads)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))

        # Get result of query and make into a list
        load_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = load_iterator.pages
        results = list(next(pages))

        # Create a "next" url page using

        if load_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        # Adds id key and value to each json slip; add next url

        for load in results:
            load["id"] = load.key.id

        output = {"loads": results}

        if next_url:
            output["next"] = next_url

        return json.dumps(output), 200

    else:
        return 'Method not recognized'


@bp.route('/<lid>', methods=['PUT', 'PATCH', 'DELETE', 'GET'])
def loads_get_put_delete(lid):
    if request.method == 'PUT':
        content = request.get_json()
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)
        load.update({"name": content["name"]})
        client.put(load)
        return '', 200

    elif request.method == 'DELETE':
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        # Checks if load with load_id exists
        if not load:
            return {"Error": "No load with this load_id exists"}, 404

        if load['carrier']:
            # Gets boat with load
            bid = load['carrier']['id']
            boat_key = client.key(constants.boats, int(bid))
            boat = client.get(key=boat_key)

            # Find index in loads list where lid is located
            boat_check = next((index for index, load in enumerate(boat['loads'])
                               if load['id'] == lid), None)

            # Delete load from loads in the boat
            del boat['loads'][boat_check]
            client.put(boat)

        return '', 204

    elif request.method == 'PATCH':

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

        # Checks if sent data is json, if not return 415
        try:
            content = request.get_json()
        except:
            # Checks if sent data is json, if not return 415
            err = {"Error": "The request header 'content_type' is not application/json "
                            "and/or the sent request body does not contain json"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 415
            return res

        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)

        # Checks if boat with boat_id exists
        if not boat:
            err = {"Error": "No boat with this boat_id exists"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

        # If any or all of the 3 attributes are provided, they are updated.
        if "name" in content and content["name"]:
            # Check value of contents to make sure they are not null or have valid characters.
            if set(content["name"]).difference(ascii_letters + whitespace):
                err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
                res = make_response(err)
                res.headers.set('Content-Type', 'application/json')
                res.status_code = 400
                return res

            # Name of boat must be unique
            query = client.query(kind=constants.boats)
            boat_list = list(query.fetch())

            # Search all boat objects and compare the names to make sure they are unique
            for curr_boat in boat_list:
                if curr_boat["name"] == content["name"]:
                    err = {"Error": "There is already a boat with that name"}
                    res = make_response(err)
                    res.headers.set('Content-Type', 'application/json')
                    res.status_code = 403
                    return res

            # Boat name is unique and updated
            boat.update({"name": content["name"]})

        if "type" in content and content["type"]:
            # Check value of contents to make sure they are not null or have valid characters.
            if set(content["type"]).difference(ascii_letters + whitespace):
                err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
                res = make_response(err)
                res.headers.set('Content-Type', 'application/json')
                res.status_code = 400
                return res

            boat.update({"type": content["type"]})

        if "length" in content and content["length"]:
            # Check value of contents to make sure they are not null or have valid characters.
            if not isinstance(content["length"], int):
                err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
                res = make_response(err)
                res.headers.set('Content-Type', 'application/json')
                res.status_code = 400
                return res

            boat.update({"length": content["length"]})

        client.put(boat)

        res = make_response()
        res.status_code = 200
        return res

    elif request.method == 'GET':

        if not request.is_json:
            # Checks if sent data is json, if not return 415
            err = err = {"Error": "The request header 'content_type' is not application/json "
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

        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        # Check if load exists
        if not load:
            return {"Error": "No load with this load_id exists"}, 404

        load["id"] = load.key.id
        load["self"] = request.base_url

        return json.dumps(load), 200

    else:
        return 'Method not recognized'
