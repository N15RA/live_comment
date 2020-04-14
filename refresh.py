import requests
import json
import time

import google.oauth2.credentials
import googleapiclient.discovery

from models import *

HOST = 'localhost'
PORT = '8080'
STREAM_ID = 'IQk5FI4kODw'

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = 'client_secret.json' # Get this from API console

from sqlservice import SQLClient
config = {
    'SQL_DATABASE_URI': 'sqlite:///data.db',
    'SQL_ISOLATION_LEVEL': 'SERIALIZABLE',
    'SQL_ECHO': False,
    'SQL_ECHO_POOL': False,
    'SQL_CONVERT_UNICODE': True,
    # 'SQL_POOL_SIZE': 5,
    # 'SQL_POOL_TIMEOUT': 30,
    # 'SQL_POOL_RECYCLE': 3600,
    # 'SQL_MAX_OVERFLOW': 10,
    'SQL_AUTOCOMMIT': False,
    'SQL_AUTOFLUSH': True,
    'SQL_EXPIRE_ON_COMMIT': True
}
db = SQLClient(config, model_class=Model)

youtube = None

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

def refresh(stream_id):
    if db.query(Token).count() == 0:
        print('Need authorize')
        return False

    # Load credentials
    token = db.query(Token).first()
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
        query = db.query(CommentHash).filter_by(hash=col_md5)
        if not query.count():
            db.session.add(CommentHash(hash=col_md5))
            db.session.add(col)
    db.session.commit()

    return True

def main():
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed >= 1.0:
            while not refresh(STREAM_ID):
                print('Retry...')
            print('Succeeded to refresh the comment: {}'.format(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')))
            start = time.time()
        time.sleep(0.5)

if __name__ == '__main__':
    main()