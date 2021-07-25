from gluon.storage import Storage
from .folders import *
from .date_utils import get_all_dates


def get_member_rec(member_id, member_rec=None, prepend_path=False):
    db, auth = inject('db', 'auth')
    if member_rec:
        rec = member_rec  # used when initially all members are loaded into the cache
    elif not member_id:
        return None
    else:
        rec = db(db.TblMembers.id == member_id).select().first()
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
    if prepend_path:
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
    s = (rec.title + ' ' if rec.title else '') + (rec.first_name or '') + ' ' + (rec.last_name or '')
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
        result[rec.id] = rec.name
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
        ids = db(db.TblTopicGroups.parent == parent).select()
        ids = [itm.child for itm in ids]
        items = db(db.TblTopics.id.belongs(ids)).select()
        for opt in items:
            result += flatten_option(opt)
    else:
        result = [option.id]
    return result


def get_tag_ids(story_id, item_type):
    db = inject('db')
    q = (db.TblItemTopics.item_type == item_type) & (db.TblItemTopics.story_id == story_id)
    lst = db(q).select()
    return [rec.topic_id for rec in lst]


def init_query(tbl, editing=False, is_deleted=False, user_id=None):
    db, auth, SV_PUBLIC, SV_ADMIN_ONLY, SV_ARCHIVER_ONLY, SV_LOGGEDIN_ONLY, ADMIN, ARCHIVER, RESTRICTED = \
        inject('db', 'auth', 'SV_PUBLIC', 'SV_ADMIN_ONLY', 'SV_ARCHIVER_ONLY', 'SV_LOGGEDIN_ONLY', 'ADMIN', 'ARCHIVER',
               'RESTRICTED')
    allowed = [SV_PUBLIC]
    user_id = auth.current_user() or user_id
    if user_id:
        allowed.append(SV_LOGGEDIN_ONLY)
        if auth.has_membership(ADMIN, user_id):
            allowed.append(SV_ADMIN_ONLY)
        if auth.has_membership(ARCHIVER, user_id):
            allowed.append(SV_ARCHIVER_ONLY)
    is_alive = not bool(is_deleted)
    q = (db.TblStories.dead != True) & (db.TblStories.deleted != is_alive)
    if tbl == db.TblStories:
        if not is_alive:
            return q
    else:
        q &= (tbl.story_id == db.TblStories.id) & (tbl.deleted != is_alive)
    if editing and auth.has_membership(RESTRICTED, user_id):
        if tbl == db.TblStories:
            q &= (tbl.author_id == user_id)
        elif tbl == db.TblPhotos or tbl == db.TblDocs or tbl == db.TblAudios:
            q &= (tbl.uploader == user_id)
        elif tbl == db.Tbl.Videos:
            q &= (tbl.contributor == user_id)
    if len(allowed) == 4:
        return q
    else:
        q &= (db.TblStories.visibility.belongs(allowed))
        return q


def get_photo_topics(story_id):
    db = inject('db')
    q = (db.TblItemTopics.story_id == story_id) & (db.TblItemTopics.item_type == 'P') & (
                db.TblTopics.id == db.TblItemTopics.topic_id)
    lst = db(q).select()
    lst = [itm.TblTopics.as_dict() for itm in lst]
    for itm in lst:
        itm['sign'] = ""
    lst = make_unique(lst, 'id')
    return lst


def get_story_topics(story_id):
    db = inject('db')
    q = (db.TblItemTopics.story_id == story_id) & (db.TblTopics.id == db.TblItemTopics.topic_id)
    lst = db(q).select()
    lst = [itm.TblTopics.as_dict() for itm in lst]
    for itm in lst:
        itm['sign'] = ""
    lst = make_unique(lst, 'id')
    return lst


def make_unique(arr, key):
    dic = dict()
    for a in arr:
        dic[a[key]] = a
    arr = [dic[id1] for id1 in sorted(dic)]
    return arr


def get_topics_query(selected_topics):
    db = inject('db')
    topic_groups = calc_grouped_selected_options(selected_topics)

    intersection = None
    for topic_group in topic_groups:
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        lst = [rec.story_id for rec in db(q1).select()]
        if intersection:
            intersection &= set(lst)
        else:
            intersection = set(lst)
    q = (db.TblStories.id.belongs(list(intersection)))
    return q


def pin_story(story_id):
    db = inject('db')
    q = (db.TblPinned.story_id == story_id)
    if db(q).isempty():
        db.TblPinned.insert(story_id=story_id)


def member_photos_by_updater(updater_id):
    db = inject('db')
    lst = db((db.TblMembers.deleted != True) & (db.TblMembers.updater_id == updater_id) & \
             (db.TblMemberPhotos.Member_id == db.TblMembers.id)). \
        select(db.TblMembers.id, db.TblMembers.first_name, db.TblMembers.last_name, db.TblMembers.updater_id,
               db.TblMemberPhotos.Photo_id, orderby=db.TblMembers.id)
    return lst


def profile_photo_path(story_id):
    db = inject('db')
    member_rec = db(db.TblMembers.story_id == story_id).select().first()
    return photos_folder('profile_photos') + (member_rec.facePhotoURL or "dummy_face.png")
