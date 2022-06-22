from .websocket_messaging import websocket_send
from .http_utils import jsondumps
from .injections import inject
from .my_cache import Cache


def messaging_group(user=None, group=None):
    if not group:
        if not user:
            auth = inject('auth')
            user = str(auth.user_id)
        group = 'USER' + str(user)
    group = Cache.fix_key(group)  # to distinguish between dev, test and www messages
    return group

def send_message(key, user=None, group=None, **data):
    request = inject('request')
    if request.is_https:
        comment = inject("comment")
        comment(f"web socket disabled until problem solved!!! key: {key}")
        return
    obj = dict(
        key=key,
        data=data
    )
    group = messaging_group(user, group)
    send_data(group, obj, key)

def try_send_message(key, user=None, group=None, **data):
    obj = dict(
        key=key,
        data=data
    )
    group = messaging_group(user, group)
    try:
        send_data(group, obj, key)
    except Exception as e:
        return f"send message failed {e}"
    return "send message was successful"


def send_data(group, obj, key):
    request = inject('request')
    host = request.env.http_host
    txt = jsondumps(obj)
    # comment('send message: group={grp} key={key} text={txt}', grp=group, key=key, txt=txt[:40])
    if request.is_https:
        h = 'wss'
        port = '8443' if host == 'tol.life' else '9443'
        key = 'sslkey'
        server_name = host
    else:
        h = 'ws'
        port = '8888'
        key = 'mykey'
        server_name = '127.0.0.1'
    websocket_send(f'{h}://{server_name}:{port}/realtime/{group}', txt, key, group)
    