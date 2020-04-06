from injections import inject
from gluon.storage import Storage
from folders import *
from date_utils import get_all_dates

def get_member_rec(member_id, member_rec=None, prepend_path=False):
    db, auth = inject('db', 'auth')
    if member_rec:
        rec = member_rec #used when initially all members are loaded into the cache
    elif not member_id:
        return None
    else:
        rec = db(db.TblMembers.id==member_id).select().first()
    if not rec:
        return None
    if rec.deleted:
        return None
    if rec.updater_id:
        rec.updater_name = auth.user_name(rec.updater_id)
    dates = get_all_dates(rec)
    rec = Storage(rec.as_dict())
    for d in dates:
        rec[d] = dates[d]
    rec.full_name = member_display_name(rec, full=True)
    rec.name = member_display_name(rec, full=False)
    if prepend_path :
        rec.facePhotoURL = photos_folder('profile_photos') + (rec.facePhotoURL or 'dummy_face.png')
    return rec

def older_display_name(rec, full):
    s = rec.Name or ''
    if full and rec.FormerName:
        s += ' ({})'.format(rec.FormerName)
    if full and rec.NickName:
        s += ' - {}'.format(rec.NickName)
    return s

def member_display_name(rec=None, member_id=None, full=True):
    rec = rec or get_member_rec(member_id)
    if not rec:
        return ''
    if not rec.first_name:
        return older_display_name(rec, full)
    s = (rec.title + ' ' if rec.title else '') + rec.first_name + ' ' + rec.last_name
    if full and (rec.former_first_name or rec.former_last_name):
        s += ' ('
        if rec.former_first_name:
            s += rec.former_first_name
        if rec.former_last_name:
            if rec.former_first_name:
                s += ' '
            s += rec.former_last_name
        s += ')'     
    if rec.NickName:
        s += ' - {}'.format(rec.NickName)
    return s

def calc_all_tags():
    result = dict()
    db = inject('db')
    for rec in db(db.TblTopics).select():
        result [rec.id] = rec.name
    return result

def calc_grouped_selected_options(option_list):
    groups = dict()
    for item in option_list:
        g = item.group_number
        if g not in groups:
            groups[g] = [item.option.sign]
        ids = flatten_option(item.option)
        groups[g] += ids
    result = []
    for g in sorted(groups):
        result.append(groups[g])
    return result

def flatten_option(option):
    db = inject('db')
    result = []
    if option.topic_kind == 1:
        parent = option.id
        ids = db(db.TblTopicGroups.parent==parent).select()
        ids = [itm.child for itm in ids]
        items = db(db.TblTopics.id.belongs(ids)).select()
        for opt in items:
            result += flatten_option(opt)
    else:
        result = [option.id]
    return result

def get_tag_ids(item_id, item_type):
    db = inject('db')
    q = (db.TblItemTopics.item_type==item_type) & (db.TblItemTopics.item_id==item_id)
    lst = db(q).select()
    return [rec.topic_id for rec in lst]

def init_query(tbl, is_deleted=False):
    db, auth, SV_PUBLIC, SV_ADMIN_ONLY, SV_ARCHIVER_ONLY, SV_LOGGEDIN_ONLY, ADMIN, ARCHIVER = \
        inject('db', 'auth', 'SV_PUBLIC', 'SV_ADMIN_ONLY', 'SV_ARCHIVER_ONLY', 'SV_LOGGEDIN_ONLY', 'ADMIN', 'ARCHIVER')
    allowed = [SV_PUBLIC]
    if auth.user:
        allowed.append(SV_LOGGEDIN_ONLY)
    for p in [ADMIN, ARCHIVER]:
        if auth.has_membership(p):
            allowed.append(p)
    is_alive = not bool(is_deleted)
    if tbl == db.TblStories:
        q = (tbl.deleted!=is_alive)
    else:
        q = (tbl.story_id==db.TblStories.id) & (tbl.deleted!=is_alive)
    if len(allowed) == 4:
        return q
    else:
        q &= (db.TblStories.visibility.belongs(allowed))
        return q

