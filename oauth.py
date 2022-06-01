from flask import Blueprint, request, redirect, make_response, render_template, url_for
from google.cloud import datastore
import constants
from google.oauth2 import id_token
from google.auth.transport import requests as req
import requests

client = datastore.Client()

bp = Blueprint('oauth', __name__, url_prefix='/oauth')


@bp.route('')
def token_user_details():
    if 'code' and 'state' not in request.args:
        return redirect(request.root_url + 'login')

    else:
        query = client.query(kind=constants.states)
        states_list = list(query.fetch())

        # Search all boat objects and compare the names to make sure they are unique
        for curr_state in states_list:
            if curr_state['state'] == request.args.get('state'):
                data = {'code': request.args.get('code'),
                        'client_id': constants.client_id,
                        'client_secret': constants.secret,
                        'redirect_uri': constants.redirect_uri,
                        'grant_type': 'authorization_code',
                        'access_type': 'offline'}

                # POST method for token
                res_token = requests.post('https://oauth2.googleapis.com/token', data=data).json()

                # Get user details
                headers = {'Authorization': 'Bearer {}'.format(res_token['access_token'])}
                res_user = requests.get(constants.people_url, headers=headers).json()

                print(res_token, res_user)

                sub = id_token.verify_oauth2_token(
                                res_token['id_token'], req.Request(), constants.client_id)['sub']

                content = None
                for e in res_user['names']:
                    if e['givenName'] and e['familyName']:
                        content = {
                            'first': e['givenName'],
                            'last': e['familyName'],
                            'jwt': res_token['id_token'],
                            'sub': sub
                        }
                    break

                # Delete state from database
                state_key = client.key(constants.states, int(curr_state.key.id))
                client.delete(state_key)

                # Name of user must be unique
                query = client.query(kind=constants.users)
                user_list = list(query.fetch())

                # Search all boat objects and compare the names to make sure they are unique
                for curr_user in user_list:
                    if curr_user["sub"] == content["sub"]:

                        # Render user page
                        return render_template('user_info.html', user=content)

                # Create new user entity
                new_user = datastore.entity.Entity(key=client.key(constants.users))
                new_user.update({"first": content["first"], "last": content["last"], "sub": content["sub"]})
                client.put(new_user)

                # If I add user_id, then add these to return also self
                # new_user["id"] = new_user.key.id
                # new_user["self"] = request.base_url + "/" + str(new_user.key.id)

                # Render user page
                return render_template('user_info.html', user=content)

        return redirect(request.root_url + 'login')
