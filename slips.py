from google.cloud import datastore
from flask import Flask, request, Blueprint
import json
import constants

client = datastore.Client()

bp = Blueprint('slips', __name__, url_prefix='/slips')


@bp.route('', methods=['POST', 'GET'])
def slips_get_post():
    if request.method == 'POST':
        content = request.get_json()

        # Check contents of the json file to make sure keys have values, and it is not empty
        if not content or "number" not in content:
            return {"Error": "The request object is missing the required number"}, 400

        # Creates new slip with number value and current_boat attribute set to None (empty)
        new_slip = datastore.entity.Entity(key=client.key(constants.slips))
        new_slip.update({"number": content["number"], "current_boat": None})
        client.put(new_slip)
        new_slip["id"] = new_slip.key.id

        return json.dumps(new_slip), 201

    elif request.method == 'GET':
        query = client.query(kind=constants.slips)
        results = list(query.fetch())

        # Adds id key and value to each json slip
        for slip in results:
            slip["id"] = slip.key.id

        return json.dumps(results), 200

    else:
        return 'Method not recognized'


@bp.route('/<slip_id>', methods=['PATCH', 'DELETE', 'GET'])
def slips_get_patch_delete(slip_id):
    if request.method == 'PATCH':
        content = request.get_json()

        # Check contents of the json file to make sure keys have values, and it is not empty
        if not content or "number" not in content:
            return {"Error": "The request object is missing at least one of the required attributes"}, 400

        slip_key = client.key(constants.slips, int(slip_id))
        slip = client.get(key=slip_key)

        # Checks slip with slip_id to see if it exists
        if not slip:
            return {"Error": "No boat with this boat_id exists"}, 404

        slip.update({"number": content["number"], "current_boat": None})
        client.put(slip)
        slip["id"] = slip.key.id

        return json.dumps(slip), 200

    elif request.method == 'DELETE':
        slip_key = client.key(constants.slips, int(slip_id))
        slip = client.get(key=slip_key)

        # Checks if slip with slip_id exists
        if not slip:
            return {"Error":  "No slip with this slip_id exists"}, 404

        client.delete(slip_key)

        return "", 204

    elif request.method == 'GET':
        slip_key = client.key(constants.slips, int(slip_id))
        slip = client.get(key=slip_key)

        # Check if slip exists
        if not slip:
            return {"Error": "No slip with this slip_id exists"}, 404

        slip["id"] = slip.key.id
        return json.dumps(slip), 200

    else:
        return 'Method not recognized'

# Handles Boats in Slips


@bp.route('/<slip_id>/<boat_id>', methods=['PUT', 'DELETE'])
def slips_put_delete(slip_id, boat_id):
    if request.method == 'PUT':

        # Gets slip
        slip_key = client.key(constants.slips, int(slip_id))
        slip = client.get(key=slip_key)

        # Gets boat
        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)

        # Check contents of the json file to make sure slip and boat exists
        if not slip or not boat:
            return {"Error":  "The specified boat and/or slip does not exist"}, 404

        if slip["current_boat"] is not None:
            return {"Error":  "The slip is not empty"}, 403

        # Find if boat_id is already parked in a
        query = client.query(kind=constants.slips)
        slip_list = list(query.fetch())

        # Adds id key and value to each json slip
        for curr_slip in slip_list:
            if curr_slip["current_boat"] == boat_id:
                return {"Error": f"The boat is already in slip: {curr_slip.key.id}"}, 403

        slip.update({"current_boat": boat.key.id})
        client.put(slip)
        return "", 204

    elif request.method == 'DELETE':
        # Gets slip
        slip_key = client.key(constants.slips, int(slip_id))
        slip = client.get(key=slip_key)

        # Gets boat
        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)

        # Check contents of the json file to make sure slip, boat exists,
        # and boat is parked at this slip
        if not slip or not boat or slip["current_boat"] != int(boat_id) or slip["current_boat"] is None:
            return {"Error":  "No boat with this boat_id is at the slip with this slip_id"}, 404

        slip.update({"current_boat": None})
        client.put(slip)

        return "", 204

    else:
        return 'Method not recognized'
