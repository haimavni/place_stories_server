from http_utils import json_to_storage
import json
from injections import inject

def read_plan():
    request = inject("request")
    app = request.application
    r = app.find("__")
    if r > 0:
        app = app[:r]
    fname = f"/apps_data/{app}/plan.txt"
    with open(fname, "r", encoding="utf-8") as f:
        data = f.read()
    obj = json.loads(data)
    result = json_to_storage(obj)
    return result


