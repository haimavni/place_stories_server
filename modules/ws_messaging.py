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
    send_data(group, obj, key)

def send_data(group, obj, key):
    request = inject('request')
    host = request.env.http_host
    txt = jsondumps(obj)
    ###comment('send message: group={grp} key={key} text={txt}', grp=group, key=key, txt=txt[:40])
    if request.is_https:
        h = 'https'
        port = '9443' if host == 'tol.life' else '8443'
        key = 'sslkeytol' if host == "tol.life" else 'sslkey'
        server_name = host
    else:
        h = 'http'
        port = '8888'
        key = 'mykey'
        server_name = '127.0.0.1'
    websocket_send('{h}://{sn}:{port}'.format(h=h, sn=server_name, port=port), txt, key, group)
