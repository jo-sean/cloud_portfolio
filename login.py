from flask import Blueprint, request, redirect, make_response
from google.cloud import datastore
from state_generator import state_gen
import constants

client = datastore.Client()

bp = Blueprint('login', __name__, url_prefix='/login')


@bp.route('', methods=['GET'])
def authorize_signin():
    if request.method == 'GET':
        # Get query of loads and set the limit and offset for the query
        # Name of boat must be unique
        new_user = datastore.entity.Entity(key=client.key(constants.states))
        new_state = state_gen()
        new_user.update({"state": new_state})
        client.put(new_user)

        oauth_url = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
                '&client_id={}&redirect_uri={}&scope={}&state={}')\
            .format(constants.client_id, constants.redirect_uri, constants.scope, new_state)

        return redirect(oauth_url)

    else:
        # Status code 405
        res = make_response()
        res.headers.set('Allow', 'GET')
        res.headers.set('Content-Type', 'text/html')
        res.status_code = 405
        return res
