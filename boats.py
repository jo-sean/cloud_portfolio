from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
import constants
from json2html import *
from string import ascii_letters, digits, whitespace

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')


@bp.route('', methods=['POST'])
def boats_get_post():
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

    if request.method == 'POST':
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

        # Check contents of the json file to make sure keys have values, and it is not empty.
        # Only supported attributes will be used. Any additional ones will be ignored.
        if not content or "name" not in content or "type" not in content or "length" not in content:
            err = {"Error": "The request object is missing at least one of the required attributes"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        # Check value of contents to make sure they are not null or have valid characters.
        if set(content["name"]).difference(ascii_letters + whitespace) or \
                set(content["type"]).difference(ascii_letters + whitespace) \
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
        new_boat.update({"name": content["name"], "type": content["type"], "length": content["length"]})
        client.put(new_boat)

        new_boat["id"] = new_boat.key.id
        new_boat["self"] = request.base_url + "/" + str(new_boat.key.id)

        res = make_response(json.dumps(new_boat))
        res.mimetype = 'application/json'
        res.status_code = 201
        return res

    # Unsure if this is necessary, since I have an else statement that will grab all unsupported methods. Check
    # rubric or ask ed if necessary
    # if request.method == 'PUT' or request.method == "DELETE":
    #     # 405 Because you are not supporting edit or delete of the entire list of boats!

    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'POST')
        res.headers.set('Content-Type', 'text/html')
        res.status_code = 405
        return res


@bp.route('/<bid>', methods=['PUT', 'PATCH', 'DELETE', 'GET'])
def boats_get_put_delete(bid):
    if request.method == 'PUT':

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

        # Check contents of the json file to make sure keys have values, and it is not empty.
        # Only supported attributes will be used. Any additional ones will be ignored.
        if not content or "name" not in content or "type" not in content or "length" not in content:
            err = {"Error": "The request object is missing at least one of the required attributes"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        # Check value of contents to make sure they are not null or have valid characters.
        if set(content["name"]).difference(ascii_letters + whitespace) or \
                set(content["type"]).difference(ascii_letters + whitespace) \
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

        # Sends the url of the object in the Location header; returns 303
        self = request.base_url
        res = make_response("")
        res.headers.set('Location', self)
        res.status_code = 303
        return res

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

        client.delete(boat_key)

        res = make_response()
        res.status_code = 204
        return res

    elif request.method == 'GET':

        if ('*/*' or 'application/json' or 'text/html') not in request.accept_mimetypes:
            # Checks if client accepts json, if not return 406
            err = {"Error": "The request header 'Accept' is not application/json or text/html"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 406
            return res

        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)

        # Check if boat exists
        if not boat:
            err = {"Error": "No boat with this boat_id exists"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

        boat["id"] = boat.key.id
        boat["self"] = request.base_url

        if ('application/json' or '*/*') in request.accept_mimetypes:
            # Sends json response
            res = make_response(json.dumps(boat))
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 200
            return res

        else:
            # Sends html response
            content = json.dumps(boat)
            res = make_response(json2html.convert(json=content))
            res.headers.set('Content-Type', 'text/html')
            res.status_code = 200
            return res

    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'GET, PUT, PATCH, DELETE')
        res.headers.set('Content-Type', 'text/html')
        res.status_code = 405
        return res
