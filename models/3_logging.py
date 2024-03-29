#import logging

import os
###logger = logging.getLogger("web2py.app.{}".format(request.application))
###logger.setLevel(logging.ERROR)
#_debugging = request.function not in ('whats_up', 'log_file_data')
#if _debugging:
    #logger.debug("\n        NEW REQUEST {}".format(request.function))
import datetime
# from misc_utils import fix_log_owner
from injections import inject
# logging.disable(logging.DEBUG)
from gluon.scheduler import logger
from folders import safe_open


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
    safe_open(base_name, 'w')
    # fix_log_owner(base_name)


def my_log(s, file_name="log_all"):
    size_limit = 400000
    path = log_path()
    fn = file_name
    app = request.application
    fname = f'{path}{fn}[{app}].log'
    file_size = os.path.getsize(fname) if os.path.exists(fname) else 0
    # need_fixing = file_size == 0
    if file_size + len(s) > size_limit:
        roll_over(fname, 10)
    ts = datetime.datetime.now()
    s1 = f"{ts}: {s}\n\n"
    try:
        with safe_open(fname, 'a') as f:
            f.write(s1)
        # if need_fixing:
            # fix_log_owner(fname)
    except:
        fname = f'{path}{fn.upper()}[{app}].log'
        with open(fname, 'a') as f:
            f.write(s1)


def log_exception_only(p, file_name='exceptions'):
    import traceback
    trace = traceback.format_exc()
    ts=datetime.datetime.now()
    s = f'{ts} Error in {p}: {trace}\n'
    my_log(s, file_name)


def log_exception(p):
    if len(p) > 300:
        p = p[:300] + ' ...'
    log_exception_only(p)
    # logger.exception(p)


def comment(s):
    my_log(s)

