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

from sqlalchemy import or_

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
CLIENT_SECRETS_FILE = 'client_secret.json' # Get this from API console
# Remember to set the SERVER_NAME

from ext_app import app
from exts import db
from models import *
from utils import credentials_to_dict
import auth
import config

from flask_migrate import Migrate
migrate = Migrate(app, db)

from flask import render_template, request, redirect, url_for

@app.route('/')
def index():
    return flask.redirect(flask.url_for('listMessage'))

@app.route('/messages')
def listMessage():
    args = flask.request.args

    stream_id = args.get('youtube', '')
    slido_hash = args.get('slido', '')

    comment_list = [i.to_dict() for i in db.query(Comment)
        .filter(or_(Comment.stream_id == stream_id, Comment.stream_id == slido_hash))
        .order_by(Comment.time.desc())
        .all()
    ]

    return flask.jsonify(comment_list)

from werkzeug.security import check_password_hash

@auth.http_basic_auth.verify_password
def verify_password(username, password):
    user = db.query(User).filter(User.username==username).first()

    if user and check_password_hash(user.password, password):
        return user
    else:
        return None

# TODO: Add unauthorized access page
@app.route('/admin', methods=['GET'])
@auth.http_basic_auth.login_required
def admin_page():        
    collector_list = db.query(Collector).all()
    return render_template('admin.html', collector=collector_list)

@app.route('/admin/addCollector', methods=['POST'])
@auth.http_basic_auth.login_required
def add_collector():
    if 'slidoInput' in request.form and request.form['slidoInput']:
        collector = Collector()
        collector.type = 'slido'
        collector.hash = request.form['slidoInput']
        db.session.add(collector)
        db.session.commit()
        
    return redirect(url_for('admin_page'))

@app.route('/admin/delCollector', methods=['POST'])
@auth.http_basic_auth.login_required
def del_collector():
    if request.form:
        for i in request.form.keys():
            slido_id = i.lstrip('slido_')
            db.query(Collector).filter(Collector.id == slido_id).delete()
            db.session.commit()

    return redirect(url_for('admin_page'))

@app.route('/authorize')
def authorize():
    # Check the CLIENT_SECRETS_FILE
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return flask.jsonify({'result': 'error', 'message': 'CLIENT_SECRETS_FILE is not set'}), 400
    
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

    if db.query(Token).count() == 0:
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
        return('Credentials successfully revoked.')
    else:
        return('An error occurred.')

@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>')

if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    ip = config.SERVER_NAME.split(':')[0]
    port = int(config.SERVER_NAME.split(':')[1], 10)
    app.run(ip, port)