import logging

import os
logger = logging.getLogger("web2py.app.{}".format(request.application))
logger.setLevel(logging.DEBUG)
_debugging = request.function not in ('whats_up', 'log_file_data')
if _debugging:
    logger.debug("\n        NEW REQUEST {}".format(request.function))
import datetime
from misc_utils import fix_log_owner
###logging.disable(logging.DEBUG)


def roll_over(base_name, max_number):
    for i in range(max_number - 1, 0, -1):
        sfn = "%s.%03d" % (base_name, i)
        dfn = "%s.%03d" % (base_name, i + 1)
        if os.path.exists(sfn):
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(sfn, dfn)
    dfn = base_name + ".001"
    if os.path.exists(dfn):
        os.remove(dfn)
    os.rename(base_name, dfn)
    fix_log_owner(base_name)

def my_log(s, file_name="log_all"):
    size_limit = 400000
    fname = '{p}{n}[{a}].log'.format(p=log_path(), n=file_name, a=request.application)
    file_size = os.path.getsize(fname) if os.path.exists(fname) else 0
    need_fixing = file_size == 0
    if file_size + len(s) > size_limit:
        roll_over(fname, 10)
    s1 = "{ts}: {s}\n\n".format(ts=datetime.datetime.now(), s=s)
    try:
        with open(fname, 'a') as f:
            f.write(s1)
        if need_fixing:
            fix_log_owner(fname)
    except:
        fname = fname = '{p}{n}[{a}].log'.format(p=log_path(), n=file_name.upper(), a=request.application)
        with open(fname, 'a') as f:
            f.write(s1)

def log_exception_only(p, file_name='exceptions'):
    import traceback
    trace = traceback.format_exc()
    s = '{ts} Error in {p}: {t}\n'.format(ts=datetime.datetime.now(), p=p, t=trace)
    my_log(s, file_name)

def log_exception(p):
    if len(p) > 300:
        p = p[:300] + ' ...'
    if isinstance(p, unicode):
        p = p.encode('utf8')
    log_exception_only(p)
    logger.exception(p)

def comment(s, *args, **kargs):
    s = s.format(*args, **kargs).replace('\n', '\n    ')
    my_log(s)

