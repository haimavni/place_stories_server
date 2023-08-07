from http_utils import json_to_storage
import json
from injections import inject

def read_plan():
    request = inject("request")
    fname = f"/apps_data/{request.application}/plan.txt"
    with open(fname, "r", encoding="utf-8") as f:
        data = f.read()
    obj = json.loads(data)
    result = json_to_storage(obj)
    return result


