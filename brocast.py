# -*- coding: utf-8 -*-
import os
import flask
import requests
import datetime
import json
import hashlib

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = 'client_secret_other.json' # Get this from API console
youtube = None

from ext_app import app
from exts import db
from models import *

def get_recent_liveChatId(stream_id):
    request = youtube.liveBroadcasts().list(
        part='snippet,contentDetails,status',
        broadcastType='all',
        maxResults=5,
        mine=True
    )
    res = request.execute()

    chat_id = None
    for r in res['items']:
        if r['id'] == stream_id:
            chat_id = r['snippet']['liveChatId']

            with open('livelist.json', 'w') as f:
                f.write(json.dumps(r))
            break
    return chat_id

def get_recent_yt_liveChat(stream_id):
    chat_id = get_recent_liveChatId(stream_id)
    if not chat_id:
        return []

    req = youtube.liveChatMessages().list(
        liveChatId=chat_id,
        part='id,snippet,authorDetails'
    )
    res = req.execute()
    with open('livechat.json', 'w') as f:
        f.write(json.dumps(res))
    chat_list = []
    for d in res['items']:
        c = {}
        c['type'] = 'youtube'
        c['icon'] = d['authorDetails']['profileImageUrl']
        c['name'] = d['authorDetails']['displayName']
        c['time'] = d['snippet']['publishedAt']
        c['comment'] = d['snippet']['displayMessage']
        chat_list.append(c)
    return chat_list

@app.route('/')
def index():
    return flask.redirect(flask.url_for('listMessage'))

@app.route('/refresh/<string:stream_id>')
def refresh(stream_id):
    if Token.query.count() == 0:
        return flask.redirect(flask.url_for('authorize'))

    # Load credentials
    token = Token.query.first()
    credentials = google.oauth2.credentials.Credentials(
        **token.credentials)

    # Build API client if necessary
    global youtube
    if not youtube:
        youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Get comment list
    chat_list = get_recent_yt_liveChat(stream_id)
    for r in chat_list:
        col = Comment()
        col.type = {'youtube': 0, 'slido': 1}[r['type']]
        col.name = r['name']
        col.icon = r['icon']
        col.text = r['comment']
        #
        ts = r['time'][:19] # strip .xxxZ
        col.time = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S')
        col.stream_id = stream_id
        #
        col_md5 = col.to_md5()
        query = CommentHash.query.filter_by(hash=col_md5)
        if not query.count():
            db.session.add(CommentHash(hash=col_md5))
            db.session.add(col)
    db.session.commit()

    return flask.jsonify(result='success', time=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'))

@app.route('/messages')
@app.route('/messages/<string:stream_id>')
def listMessage(stream_id=None):
    if Token.query.count() == 0:
        return flask.redirect(flask.url_for('authorize'))
    # TODO: make load/save credentials to func decorator
    # Load credentials
    token = Token.query.first()
    credentials = google.oauth2.credentials.Credentials(
        **token.credentials)

    # Save credentials
    token = Token.query.first()
    token.credentials = credentials_to_dict(credentials)
    db.session.commit()

    comment_list = [i.to_dict() for i in Comment.query.filter_by(stream_id=stream_id).all()]
    return flask.jsonify(comment_list)

@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    if Token.query.count() == 0:
        token = Token(credentials=credentials_to_dict(credentials))
        db.session.add(token)
        db.session.commit()

    return flask.redirect(flask.url_for('index'))


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return('Credentials successfully revoked.' + print_index_table())
    else:
        return('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>' +
            print_index_table())


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

def print_index_table():
    return ('<table>' +
            '<tr><td><a href="/test">Test an API request</a></td>' +
            '<td>Submit an API request and see a formatted JSON response. ' +
            '    Go through the authorization flow if there are no stored ' +
            '    credentials for the user.</td></tr>' +
            '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
            '<td>Go directly to the authorization flow. If there are stored ' +
            '    credentials, you still might not be prompted to reauthorize ' +
            '    the application.</td></tr>' +
            '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
            '<td>Revoke the access token associated with the current user ' +
            '    session. After revoking credentials, if you go to the test ' +
            '    page, you should see an <code>invalid_grant</code> error.' +
            '</td></tr>' +
            '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
            '<td>Clear the access token currently stored in the user session. ' +
            '    After clearing the token, if you <a href="/test">test the ' +
            '    API request</a> again, you should go back to the auth flow.' +
            '</td></tr></table>')


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run('localhost', 8080, debug=True)