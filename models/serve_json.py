import json
from http_utils import json_to_storage
import datetime

class User_Error(Exception): #todo: the "_" is because of soon obsolete code. remove it when 

    def __init__(self, message, location=None):
        Exception.__init__(self, message)
        self.location = location

def serve_json(func):

    def f():
        s = request.body.read()
        if len(s) > 0:
            comment("non empty body")
            y = json.loads(s)
            vars = json_to_storage(y)
        else:
            vars = request.vars
            comment(f"request.function: {request.function} {len(vars)} vars")
        for k in vars:
            s = vars[k]
            comment(f"k is {k}, s is {s}")
            if isinstance(s, str) and (s.startswith('{') or s.startswith('[')):
                vars[k] = json.loads(s)
        vars = json_to_storage(vars)
        # comment(f"about to call {func.__name__}")
        try:
            result = func(vars)
            if result is None:
                result = dict()
        except HTTP as e:
            if e.status == 303:
                return response.json(e.headers)
            else:
                log_exception('Error serving ' + func.__name__)
                return json.dumps(dict(error=str(e)))
        except User_Error as e:
            log_exception('User error serving ' + func.__name__)
            return json.dumps(dict(user_error=str(e)))
        except Exception as e:
            log_exception('Error serving ' + func.__name__)
            return json.dumps(dict(error=repr(e)))
        try:
            result = response.json(result)
        except Exception as e:
            result = dict(warning=str(e), result=str(result))
            result = json.dumps(result)
        # comment(f"finished calling {func.__name__}")
        return result

    return f