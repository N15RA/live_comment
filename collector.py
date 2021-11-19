import click
import requests
import json
import time
import multiprocessing

import google.oauth2.credentials
import googleapiclient.discovery

from models import *

HOST = 'localhost'
PORT = '8080'

YT_STREAM_ID = 'IQk5FI4kODw'
SLIDO_EVENT_HASH = 'gwbbskoz'

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
    'SQL_AUTOFLUSH': False,
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

from utils import credentials_to_dict
from functools import wraps
def need_authorize(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if db.query(Token).count() == 0:
            return False
            # return flask.redirect(flask.url_for('authorize'))
        # Load credentials
        token = db.query(Token).first()
        credentials = google.oauth2.credentials.Credentials(
            **token.credentials)
        # Call the actual function
        kwargs['credentials'] = credentials
        retVal = func(*args, **kwargs)
        #
        token = db.query(Token).first()
        token.credentials = credentials_to_dict(credentials)
        db.session.commit()
        #
        return retVal
    return wrapper

@need_authorize
def refresh_yt(stream_id, credentials=None):
    try:
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
    # TODO: Handle exception properly
    except Exception as e:
        return False
    return True

# ---------------------------------------------------------------------------------

def get_slido_event_uuid(hash):
    # Get event info
    event_info = requests.get('https://app.sli.do/api/v0.5/events?hash={}'.format(hash)).json()
    # print(event_info)
    event_info = event_info[0]
    # Update uuid
    event_uuid = event_info['uuid']
    return event_uuid

# Get user auth info
def get_slido_auth_token(event_uuid):
    user = requests.post(f'https://app.sli.do/api/v0.5/events/{event_uuid}/auth').json()
    # print(user)
    return user['access_token']

# sort = top|newest|oldest
# limit >= 1
def get_slido_comments(event_hash, event_uuid, access_token, sort='newest', limit=9999):
    comment_list = requests.get(f'https://app.sli.do/api/v0.5/events/{event_uuid}/questions?sort={sort}&limit={limit}', headers={
        'Authorization': f'Bearer {access_token}'
    }).json()
    #
    for c in comment_list:
        r = Comment(
            type=1,
            name=c['author'].get('name', None) or 'Anonymous',
            text=c['text'],
            time=datetime.datetime.strptime(c['date_updated'][:19], '%Y-%m-%dT%H:%M:%S'),
            stream_id=event_hash
        )
        # Check hash
        if not db.query(CommentHash).filter_by(hash=r.to_md5()).count():
            # Add comment
            db.session.add(r)
            db.session.commit()
            # Add hash
            db.session.add(CommentHash(hash=r.to_md5()))
            db.session.commit()

# hash = event hash
event_uuid = None
access_token = None
def refresh_slido(hash):
    print('Refresh slido {}'.format(hash))
    try:
        # Update event uuid
        global event_uuid
        if not event_uuid:
            event_uuid = get_slido_event_uuid(hash)
        # Update access token
        global access_token
        if not access_token:
            access_token = get_slido_auth_token(event_uuid)
        # Update slido comment to db
        get_slido_comments(hash, event_uuid, access_token)
    # TODO: Handle exception properly
    except Exception as e:
        print(e)
        print(e.args)
        return False
    return True

# ---------------------------------------------------------------------------------

def refresh_yt_with_retry(stream_id, credentials=None):
    pass_flag = True
    while not refresh_yt(youtube):
        cnt += 1
        print('Retry youtube')
        if cnt >= 3:
            cnt = 0
            pass_flag = False
            break
    return pass_flag

def refresh_slido_with_retry(slido):
    pass_flag = True
    while not refresh_slido(slido):
        cnt += 1
        print('Retry slido')
        if cnt >= 3:
            cnt = 0
            pass_flag = False
            break
        time.sleep(0.5)
    return pass_flag

def refresh_collector(collector: Collector):
    while True:
        if collector.type == 'slido':
            refresh_slido_with_retry(collector.hash)
        elif collector.type == 'youtube':
            print('TODO')
            
        time.sleep(5)

if __name__ == '__main__':
    #
    worker = {}
    
    while True:
        c = db.query(Collector).all()
    
        for i in c:
            if i.id not in worker:
                worker[i.id] = multiprocessing.Process(target=refresh_collector, args=(i,))
                worker[i.id].start()
                print('Started worker for collector {} type={}'.format(i.id, i.type))
                
        time.sleep(1)
