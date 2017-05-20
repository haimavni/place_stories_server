import requests
from gluon.storage import Storage
import datetime
import json

def build_url(base_url, *args, **kwargs):
    url = base_url
    for arg in args:
        url += '/' + arg
    url += '?'
    for k in sorted(kwargs):
        if kwargs[k]:
            url += k + '=' + str(kwargs[k]) + '&'
    return url[:-1]

def read_url(url,**kwargs):
    s = requests.get(url, **kwargs)
    if not s.ok:
        msg = 'Request {u} returned status {s}: {r}. {w}'.format(u=url, s=s.status_code, r=s.reason, w=s.text)
        raise Exception(msg)
    result = json_to_storage(s.json)
    return result

unreserve = {
    'class': 'Class',
    'global': 'Global',
    'from': 'From',
    'values': 'Values'
    }

def normalize(k):
    k = k.replace('$', '__')
    k = unreserve.get(k, k)
    if k.startswith('_'):
        k = 'z' + k
    return k

def json_to_storage(data):
    if isinstance(data, (tuple, list)):
        for i, elem in enumerate(data):
            data[i] = json_to_storage(elem)
    elif isinstance(data, dict):
        for k, v in data.items():
            k1 = normalize(k)
            data[k1] = json_to_storage(v)
            if k != k1:
                del data[k]
    if isinstance(data, dict):
        return Storage(data)
    elif isinstance(data, unicode):
        return data.encode('utf8')
    elif callable(data):
        data1 = data()
        return json_to_storage(data1)
    else:
        return data

def default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.isoformat()

def jsondumps(o):
    return json.dumps(o, default=default)    
