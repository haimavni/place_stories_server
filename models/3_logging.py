import logging
logger = logging.getLogger("web2py.app.{}".format(request.application))
logger.setLevel(logging.DEBUG)

_debugging = request.function not in ('whats_up', 'log_file_data')
if _debugging:
    logger.debug("\n        NEW REQUEST {}".format(request.function))
logging.disable(logging.DEBUG)

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

def log_exception_only(p, file_name='exceptions'):
    import traceback
    size_limit = 400000
    trace = traceback.format_exc()
    fname = 'applications/' + request.application + '/logs/{}.log'.format(file_name)
    s = '{ts} Error in {p}: {t}\n'.format(ts=datetime.datetime.now(), p=p, t=trace)
    file_size = os.path.getsize(fname) if os.path.exists(fname) else 0
    if file_size + len(s) > size_limit:
        roll_over(fname, 10)
    with open(fname, 'a') as f:
        f.write(s)

def log_exception(p):
    if len(p) > 300:
        p = p[:300] + ' ...'
    if isinstance(p, unicode):
        p = p.encode('utf8')
    log_exception_only(p)
    logger.exception(p)

def comment(s, *args, **kargs):
    s = s.format(*args, **kargs).replace('\n', '\n    ')
    logger.debug('\n    ' + s)

