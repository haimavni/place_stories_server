from injections import inject
from gluon.storage import Storage
from photos_support import photos_folder
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
    s = rec.first_name + ' ' + rec.last_name
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
    option_list = flatten_option_list(option_list)
    groups = dict()
    for item in option_list:
        g = item.group_number
        if g not in groups:
            groups[g] = [item.option.sign]
        groups[g].append(item.option.id)
    result = []
    for g in sorted(groups):
        result.append(groups[g])
    return result

def flatten_option_list(option_list):
    db = inject('db')
    result = []
    for item in option_list:
        if item.option.is_group:
            parent = item.option.id
            ids = db(db.TblTopicGroups.parent==parent).select()
            items = [Storage(group_number=item.group_number, option=Storage(sign=item.option.sign, id=r.child)) for r in ids]
            result += flatten_option_list(items)
        else:
            result.append(item)
    return result

def get_tag_ids(item_id, item_type):
    db = inject('db')
    q = (db.TblItemTopics.item_type==item_type) & (db.TblItemTopics.item_id==item_id)
    lst = db(q).select()
    return [rec.topic_id for rec in lst]


