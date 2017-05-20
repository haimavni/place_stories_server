from gluon.contrib.websocket_messaging import websocket_send
import simplejson
from injections import inject
from my_cache import Cache
from http_utils import jsondumps

def messaging_group(user=None, group=None):
    if not group:
        if not user:
            auth = inject('auth')
            user = str(auth.user_id)
        group = 'USER' + str(user)
    group = Cache.fix_key(group) #to distinguish between dev, test and www messages
    return group

def send_message(key, user=None, group=None, **data):
    obj = dict(
        key=key,
        data=data
    )
    group = messaging_group(user, group)
    send_data(group, obj)

def send_data(group, obj):
    txt = jsondumps(obj)
    ###txt = simplejson.dumps(obj)
    websocket_send('http://127.0.0.1:8888', txt, 'mykey', group)
