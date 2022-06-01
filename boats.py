from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
import constants
from json2html import *
from string import ascii_letters, digits, whitespace
from google.oauth2 import id_token
from google.auth.transport import requests

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')


def check_jwt(headers):
    # Checks if JWT was provided in Authorization header
    if 'Authorization' in headers:
        auth_header = request.headers['Authorization']
        auth_header = auth_header.split(" ")[1]

        # Checks validity of JWT provided
        try:
            sub = id_token.verify_oauth2_token(
                auth_header, requests.Request(), constants.client_id)['sub']
            return sub
        except:
            err = {"Error": "JWT is invalid"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 401
            return res
    else:
        err = {"Error": "Authorization header is missing JWT"}
        res = make_response(err)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 401
        return res


@bp.route('', methods=['POST', 'GET'])
def boats_get_post():
    # Checks if JWT was provided in Authorization header
    sub = check_jwt(request.headers)

    if not isinstance(sub, str):
        return sub

    if request.method == 'POST':
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

        # Checks if header sent data is json, if not return 415
        try:
            content = request.get_json()
        except:
            err = {"Error": "The request header 'content_type' is not application/json "
                            "and/or the sent request body does not contain json"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 415
            return res

        # Check contents of the json file to make sure keys have values, and it is not empty.
        # Only supported attributes will be used. Any additional ones will be ignored.
        if not content or "name" not in content or "type" not in content or "length" not in content:
            err = {"Error": "The request object is missing at least one of the required attributes"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        # Check value of contents to make sure they are not null or have valid characters.
        if set(content["name"]).difference(ascii_letters + digits + whitespace) or \
                set(content["type"]).difference(ascii_letters + digits + whitespace) \
                or not isinstance(content["length"], int):
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

        # Create new boat entity
        new_boat = datastore.entity.Entity(key=client.key(constants.boats))
        new_boat.update({"name": content["name"], "type": content["type"], "length": content["length"],
                         "loads": [], "owner": sub})

        client.put(new_boat)
        new_boat["id"] = new_boat.key.id
        new_boat["self"] = request.base_url + "/" + str(new_boat.key.id)

        res = make_response(json.dumps(new_boat))
        res.mimetype = 'application/json'
        res.status_code = 201
        return res

    elif request.method == 'GET':

        if ('*/*' or 'application/json') not in request.accept_mimetypes:
            # Checks if client accepts json, if not return 406
            err = {"Error": "The request header 'Accept' is not application/json"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 406
            return res

        # Get query of boats by owner and set the limit and offset for the query
        query = client.query(kind=constants.boats)
        query.add_filter("owner", "=", sub)
        total_boats = list(query.fetch())
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))

        # Get result of query and make into a list
        boat_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = boat_iterator.pages
        results = list(next(pages))

        # Create a "next" url page using
        if boat_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        # Adds id key and value to each json slip; add next url
        for boat in results:
            boat["id"] = boat.key.id
            boat["self"] = request.base_url + "/" + str(boat.key.id)
        output = {"boats": results}

        if next_url:
            output["next"] = next_url

        output["total_boats"] = len(total_boats)

        res = make_response(json.dumps(output))
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 200
        return res

    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'GET, POST')
        res.headers.set('Content-Type', 'text/html')
        res.status_code = 405
        return res


@bp.route('/<bid>', methods=['PATCH', 'PUT', 'DELETE', 'GET'])
def boats_get_put_delete(bid):
    # Checks if JWT was provided in Authorization header
    sub = check_jwt(request.headers)

    if not isinstance(sub, str):
        return sub

    if request.method == 'PATCH':

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

        elif boat["owner"] != sub:
            err = {"Error": "The boat is owned by another user"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 403
            return res

        # If any or all of the 3 attributes are provided, they are updated.
        if "name" in content and content["name"]:
            # Check value of contents to make sure they are not null or have valid characters.
            if set(content["name"]).difference(ascii_letters + digits + whitespace):
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
            if set(content["type"]).difference(ascii_letters + digits + whitespace):
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

    elif request.method == 'PUT':

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

        elif boat["owner"] != sub:
            err = {"Error": "The boat is owned by another user"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 403
            return res

        # Check contents of the json file to make sure keys have values, and it is not empty.
        # Only supported attributes will be used. Any additional ones will be ignored.
        if not content or "name" not in content or "type" not in content or "length" not in content:
            err = {"Error": "The request object is missing at least one of the required attributes"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        # Check value of contents to make sure they are not null or have valid characters.
        if set(content["name"]).difference(ascii_letters + digits + whitespace) or \
                set(content["type"]).difference(ascii_letters + digits + whitespace) \
                or not isinstance(content["length"], int):
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

        # Edits all the attributes, except the id
        boat.update({"name": content["name"], "type": content["type"], "length": content["length"]})
        client.put(boat)

        res = make_response()
        res.status_code = 200
        return res

    elif request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)

        # Checks if boat with boat_id exists
        if not boat:
            err = {"Error": "No boat with this boat_id exists"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

        elif boat["owner"] != sub:
            err = {"Error": "The boat is owned by another user"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 403
            return res

        # Check to see if load(s) is/are on the boat; remove load(s) (carrier==None)
        query = client.query(kind=constants.loads)
        loads_list = list(query.fetch())

        for curr_load in loads_list:
            if curr_load["carrier"] and curr_load["carrier"]['id'] == bid:
                curr_load.update({"carrier": None})
                client.put(curr_load)

        client.delete(boat_key)

        res = make_response()
        res.status_code = 204
        return res

    elif request.method == 'GET':

        if ('*/*' or 'application/json') not in request.accept_mimetypes:
            # Checks if client accepts json, if not return 406
            err = {"Error": "The request header 'Accept' is not application/json"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 406
            return res

        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)

        # Check if boat exists
        if not boat:
            return {"Error": "No boat with this boat_id exists"}, 404

        boat["id"] = boat.key.id
        boat["self"] = request.base_url

        # Sends json response
        res = make_response(json.dumps(boat))
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 200
        return res

    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'GET, DELETE')
        res.headers.set('Content-Type', 'text/html')
        res.status_code = 405
        return res


@bp.route('/<bid>/loads/<lid>', methods=['PUT', 'DELETE'])
def put_delete_loads_in_boat(bid, lid):
    # Checks if JWT was provided in Authorization header
    sub = check_jwt(request.headers)

    if not isinstance(sub, str):
        return sub

    if request.method == 'PUT':

        # Gets boat
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)

        # Gets load
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        # Check contents of the json file to make sure slip and boat exists
        if not load or not boat:
            err = {"Error": "The specified boat and/or load does not exist"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

        elif load["carrier"]:
            err = {"Error": "The load is already loaded on another boat"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 403
            return res

        elif boat["owner"] != sub:
            err = {"Error": "The boat is owned by another user"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 403
            return res

        else:
            boat['loads'].append({"id": lid, "self": request.root_url + "loads/" + str(load.key.id)})
            load['carrier'] = {"id": bid, "name": boat['name'], "self": request.root_url + "boats/" + str(boat.key.id)}

        client.put(boat)
        client.put(load)

        res = make_response()
        res.status_code = 204
        return res

    elif request.method == 'DELETE':

        # Gets load
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        # Gets boat
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        boat_check = None

        if boat:
            boat_check = next((index for index, load in enumerate(boat['loads'])
                               if load['id'] == lid), None)

        # Check contents of the json file to make sure slip, boat exists,
        # and boat is parked at this slip
        if not load or not boat or load["carrier"] is None or \
                load["carrier"]['id'] != bid or boat["loads"] == [] or \
                boat_check is None:

            err = {"Error": "No boat with this boat_id is loaded with the load with this load_id"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

        elif boat["owner"] != sub:
            err = {"Error": "The boat is owned by another user"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 403
            return res

        else:
            del boat['loads'][boat_check]
            load["carrier"] = None
            client.put(boat)
            client.put(load)

            res = make_response()
            res.status_code = 204
            return res

    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'GET, DELETE')
        res.headers.set('Content-Type', 'text/html')
        res.status_code = 405
        return res


@bp.route('/<bid>/loads', methods=['GET'])
def get_reservations(bid):
    # Checks if JWT was provided in Authorization header
    sub = check_jwt(request.headers)

    if not isinstance(sub, str):
        return sub

    boat_key = client.key(constants.boats, int(bid))
    boat = client.get(key=boat_key)
    load_list = {"self": request.root_url + "boats/" + bid, "loads": []}

    # Check if boat exists
    if not boat:
        err = {"Error": "No boat with this boat_id exists"}
        res = make_response(err)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 404
        return res

    # Checks ownership of boat
    elif boat["owner"] != sub:
        err = {"Error": "The boat is owned by another user"}
        res = make_response(err)
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 403
        return res

    if boat['loads']:
        for load in boat['loads']:
            load_list['loads'].append(load)

            # Sends json response
            res = make_response(json.dumps(load_list))
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 200
            return res

    # Boat has no loads
    else:
        # Sends json response
        res = make_response(json.dumps([]))
        res.headers.set('Content-Type', 'application/json')
        res.status_code = 200
        return res
