from flask import Blueprint, request, redirect, make_response, render_template, url_for
from google.cloud import datastore
import json
import constants
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

                user = None
                for e in res_user['names']:
                    if e['givenName'] and e['familyName']:

                        user = {
                            'first': e['givenName'],
                            'last': e['familyName'],
                            'jwt': res_token['id_token']
                        }

                    break

                # Delete state from database
                state_key = client.key(constants.states, int(curr_state.key.id))
                client.delete(state_key)

                # return redirect(request.root_url + 'user' + '/' + curr_state['state'])
                return render_template('user_info.html', user=user)

        return redirect(request.root_url + 'login')
