# ---script for developer to evaluate python expressions in the environment
import datetime


@serve_json
def load_script(vars):
    prev_code, next_code = prev_next_code()
    code = prev_code or next_code
    prev_disabled = prev_code == ''
    next_disabled = next_code == ''
    return dict(code=code, prev_disabled=prev_disabled, next_disabled=next_disabled)


@serve_json
def evaluate_script(vars):
    code = vars.code
    if not code:
        raise User_Error('Code is empty!')
    environment = globals()
    old_environment = dict(environment)
    try:
        ccode = compile(code.replace('\r\n', '\n'), 'Script', 'exec')
    except Exception as e:
        return dict(error=repr(e))
    try:
        exec(ccode, environment)
        dic = dict()
        for v in environment:
            if v not in old_environment or environment[v] != old_environment[v]:
                x = environment[v]
                t = type(x)
                comment(f"=======type of x: {t}")
                dic[v] = environment[v]
    except Exception as e:
        log_exception('Error in ad-hoc script')
        dic = dict(error=str(e))
        return dict(results=dic)
    else:
        rec = db(db.scripts_table.code == code).select().first()
        now = datetime.datetime.now()
        if rec:
            rec.update_record(last_usage_time=now)
        else:
            db.scripts_table.insert(code=code, last_usage_time=now)
        return dict(results=dic)


@serve_json
def prev_code(vars):
    prev_code, next_code = prev_next_code(vars.code, vars.like)
    code = prev_code
    prev_code, next_code = prev_next_code(code, vars.like)
    return dict(code=code, prev_disabled=prev_code == '', next_disabled=next_code == '')


@serve_json
def next_code(vars):
    prev_code, next_code = prev_next_code(vars.code, vars.like)
    code = next_code
    prev_code, next_code = prev_next_code(code, vars.like)
    return dict(code=code, prev_disabled=prev_code == '', next_disabled=next_code == '')


@serve_json
def delete(vars):
    db(db.scripts_table.code == vars.code).delete()
    prev_code, next_code = prev_next_code(vars.code, vars.like)
    code = prev_code
    prev_code, next_code = prev_next_code(code, vars.like)
    return dict(code=code, prev_disabled=prev_code == '', next_disabled=next_code == '')


def likes_query(like):
    likes = like.split(' ') if like else []
    q = None
    for like in likes:
        like = '%' + like + '%'
        q1 = db.scripts_table.code.like(like)
        q = q & q1 if q else q1
    return q


def prev_next_code(code=None, like=None):
    rec = db(db.scripts_table.code == code).select().first() if code else None
    if not rec:
        q = db.scripts_table.id > 0
        rec = db(q).select(orderby=db.scripts_table.last_usage_time).last()
        if rec:
            return rec.code, ''
        else:
            return '', ''
    q_prev = (db.scripts_table.last_usage_time < rec.last_usage_time)
    q_next = (db.scripts_table.last_usage_time > rec.last_usage_time)
    q_likes = likes_query(like)
    if q_likes:
        q_prev &= q_likes
        q_next &= q_likes
    rec_prev = db(q_prev).select(orderby=db.scripts_table.last_usage_time).last()
    rec_next = db(q_next).select(orderby=db.scripts_table.last_usage_time).first()
    return (rec_prev.code if rec_prev else ''), (rec_next.code if rec_next else '')
