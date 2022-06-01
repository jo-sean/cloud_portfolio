from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
from datetime import datetime
from string import ascii_letters, digits, whitespace
import constants

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')


@bp.route('', methods=['POST', 'GET'])
def loads_get_post():
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

        content = request.get_json()

        # Check value of contents to make sure they are not null or have valid characters.
        if set(content["item"]).difference(ascii_letters + digits + whitespace) \
                or not isinstance(content["volume"], int) or len(content["creation_date"]) != 10:
            err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        # Check date format
        date_format = "%m/%d/%Y"
        try:
            datetime.strptime(content["creation_date"], date_format)
        except ValueError:
            err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        new_load.update({"volume": content["volume"], "carrier": None, "item": content["item"],
                         "creation_date": content["creation_date"]})
        client.put(new_load)

        new_load["id"] = new_load.key.id
        new_load["self"] = request.base_url + "/" + str(new_load.key.id)

        res = make_response(json.dumps(new_load))
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

        # Get query of loads and set the limit and offset for the query
        query = client.query(kind=constants.loads)
        total_loads = list(query.fetch())
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
            load["self"] = request.base_url + "/" + str(load.key.id)

        output = {"loads": results}

        # There is a next_url
        if next_url:
            output["next"] = next_url

        output["total_loads"] = len(total_loads)

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


@bp.route('/<lid>', methods=['PUT', 'PATCH', 'DELETE', 'GET'])
def loads_get_put_delete(lid):
    if request.method == 'PUT':

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

        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        # Checks if boat with boat_id exists
        if not load:
            err = {"Error": "No boat with this load_id exists"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

        # Check contents of the json file to make sure keys have values, and it is not empty.
        # Only supported attributes will be used. Any additional ones will be ignored.
        if not content or "volume" not in content or "item" not in content or "creation_date" not in content:
            err = {"Error": "The request object is missing at least one of the required attributes"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        # Check value of contents to make sure they are not null or have valid characters.
        if set(content["item"]).difference(ascii_letters + digits + whitespace) \
                or not isinstance(content["volume"], int) or len(content["creation_date"]) != 10:
            err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        # Check date format
        date_format = "%m/%d/%Y"
        try:
            datetime.strptime(content["creation_date"], date_format)
        except ValueError:
            err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 400
            return res

        load.update({"volume": content["volume"], "item": content["item"],
                     "creation_date": content["creation_date"]})
        client.put(load)

        res = make_response()
        res.status_code = 200
        return res

    elif request.method == 'DELETE':
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        # Checks if load with load_id exists
        if not load:
            err = {"Error": "No load with this load_id exists"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

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

        client.delete(load_key)

        res = make_response()
        res.status_code = 204
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

        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        # Checks if boat with boat_id exists
        if not load:
            err = {"Error": "No load with this load_id exists"}
            res = make_response(err)
            res.headers.set('Content-Type', 'application/json')
            res.status_code = 404
            return res

        # If any or all of the 3 attributes are provided, they are updated.
        if "item" in content and content["item"]:
            # Check value of contents to make sure they are not null or have valid characters.
            if set(content["item"]).difference(ascii_letters + digits + whitespace):
                err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
                res = make_response(err)
                res.headers.set('Content-Type', 'application/json')
                res.status_code = 400
                return res

            # Load name is updated
            load.update({"item": content["item"]})

        if "volume" in content and content["volume"]:
            # Check value of contents to make sure they are not null or have valid characters.
            if not isinstance(content["volume"], int):
                err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
                res = make_response(err)
                res.headers.set('Content-Type', 'application/json')
                res.status_code = 400
                return res

            load.update({"volume": content["volume"]})

        if "creation_date" in content and content["creation_date"]:
            # Check value of contents to make sure they are not null or have valid characters.

            date_format = "%m/%d/%Y"

            if len(content["creation_date"]) != 10:
                err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
                res = make_response(err)
                res.headers.set('Content-Type', 'application/json')
                res.status_code = 400
                return res

            try:
                datetime.strptime(content["creation_date"], date_format)
            except ValueError:
                err = {"Error": "The request object has at least one invalid value assigned to an attribute"}
                res = make_response(err)
                res.headers.set('Content-Type', 'application/json')
                res.status_code = 400
                return res

            load.update({"creation_date": content["creation_date"]})

        client.put(load)

        res = make_response()
        res.status_code = 200
        return res

    elif request.method == 'GET':

        if 'application/json' not in request.accept_mimetypes:
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

        # Sends json response
        res = make_response(json.dumps(load))
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
