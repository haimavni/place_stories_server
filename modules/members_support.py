from gluon.storage import Storage
from .folders import *
from .date_utils import get_all_dates
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS
import stories_manager


def get_member_rec(member_id, member_rec=None, prepend_path=False):
    db, auth, comment, NO_DATE, RESTRICTED = inject('db', 'auth', 'comment', 'NO_DATE', 'RESTRICTED')
    is_dead = False
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
    editing_ok = True
    editing_ok = auth.current_user() == rec.updater_id or not auth.has_membership(RESTRICTED)
    rec.editing_ok = editing_ok
    is_dead = (rec.date_of_death != NO_DATE) & (rec.date_of_death != None)
    dates = get_all_dates(rec)
    rec = Storage(rec.as_dict())
    for d in dates:
        rec[d] = dates[d]
    rec.full_name = member_display_name(rec, full=True)
    rec.name = member_display_name(rec, full=False)
    if rec.story_id:
        handle_bio_name(rec)
    if prepend_path:
        rec.facephotourl = photos_folder(PROFILE_PHOTOS) + (rec.facephotourl or 'dummy_face.png')
    if is_dead:
        rec.life_status = "dead"
    else:
        rec.life_status = "alive"
    return rec

def handle_bio_name(rec):
    db = inject("db")
    rec = db(db.TblStories.id==rec.story_id).select().first()
    if not rec.name:
        rec.update_record(name=rec.name)
    rec.has_bio_text = len(rec.story) > 0

def older_display_name(rec, full):
    s = rec.name or ''
    if full and rec.formername:
        s += ' ({})'.format(rec.formername)
    if full and rec.nickname:
        s += ' - {}'.format(rec.nickname)
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
    if rec.nickname:
        s += ' - {}'.format(rec.nickname)
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
        q &= (tbl.story_id == db.TblStories.id) & (db.TblStories.deleted != is_alive)
    if editing and auth.has_membership(RESTRICTED, user_id):
        if tbl == db.TblStories:
            q &= (db.TblStories.author_id == user_id)
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
    return get_object_topics(story_id, 'P')


def get_object_topics(story_id, typ):
    db = inject('db')
    q = (db.TblItemTopics.story_id == story_id) & (db.TblItemTopics.item_type == typ) & (
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
             (db.TblMemberPhotos.member_id == db.TblMembers.id)). \
        select(db.TblMembers.id, db.TblMembers.first_name, db.TblMembers.last_name, db.TblMembers.updater_id,
               db.TblMemberPhotos.photo_id, orderby=db.TblMembers.id)
    return lst


def profile_photo_path(story_id):
    db, comment = inject('db', 'comment')
    member_rec = db(db.TblMembers.story_id == story_id).select().first()
    if not member_rec:
        comment(f"story id={story_id} has no member")
    if member_rec and member_rec.facephotourl:
        fname = member_rec.facephotourl
    else:
        fname = "dummy_face.png"
    return photos_folder(PROFILE_PHOTOS) + fname

def check_dups():
    db = inject('db')
    lst = db(db.TblMembers.last_name.like("% ")).select(db.TblMembers.id, db.TblMembers.last_name)
    for mem in lst:
        mem.update_record(last_name = mem.last_name.strip())
    dic = dict()
    for member in db(db.TblMembers.deleted==False).select(db.TblMembers.id, db.TblMembers.first_name, db.TblMembers.last_name):
        name = (member.first_name or '') + ' ' + (member.last_name or '')
        if name not in dic:
            dic[name] = []
        dic[name].append(member.id)
    duplicates = []
    for itm in dic:
        if len(itm) < 2:
            continue
        if len(dic[itm]) > 1:
            duplicates.append(dic[itm])
    return duplicates

def set_story_sorting_keys(refresh=False):
    db, STORY4MEMBER = inject('db', 'STORY4MEMBER')
    if refresh:
        db(db.TblStories.deleted != True).update(sorting_key = None)
    q = (db.TblStories.deleted != True) & \
        (db.TblStories.used_for==STORY4MEMBER) & \
        (db.TblStories.sorting_key==None) & \
        (db.TblMembers.story_id==db.TblStories.id)
    nms = 0
    for rec in db(q).select():
        nms += 1
        story_rec = rec.TblStories
        member_rec = rec.TblMembers
        key = (member_rec.last_name or '') + ' ' + (member_rec.first_name or '')
        story_rec.update_record(sorting_key=key)
    q = (db.TblStories.deleted != True) & \
        (db.TblStories.sorting_key==None) & \
        (db.TblStories.used_for != STORY4MEMBER)
    ns = 0
    for rec in db(q).select():
        ns += 1
        rec.update_record(sorting_key=rec.name)
    return dict(ns=ns, nms=nms)

def new_bio(name):
    STORY4MEMBER = inject("STORY4MEMBER")
    sm = stories_manager.Stories()
    story_info = sm.get_empty_story(used_for=STORY4MEMBER, story_text="", name=name)
    result = sm.add_story(story_info)
    return result.story_id

def attach_bio_to_member(member_rec):
    if member_rec.story_id:
        return
    name = (member_rec.first_name or "") + " " + (member_rec.last_name or "")
    name = name.strip()
    story_id = new_bio(name)
    member_rec.update_record(story_id=story_id)
    
def add_missing_bios():
    db = inject("db")
    q = (db.TblMembers.deleted!=True) & (db.TblMembers.story_id==None)
    for member_rec in db(q).select():
        attach_bio_to_member(member_rec)
        
def add_story_id_to_hits():
    db = inject("db")
    tables = [
        'MEMBER',
        'EVENT',
        'STORY',
        'PHOTO',
        'TERM',
        'DOC',
        'DOCSEG',
        'VIDEO'
    ]
    for what in tables:
        lst = db((db.TblPageHits.story_id==None) & (db.TblPageHits.what==what)).select()
        for hit_rec in lst:
            story_id, item_id = calc_hit_story_id(what, hit_rec.item_id)
            hit_rec.update_record(story_id=story_id, item_id=item_id)
                
def calc_hit_story_id(what, item_id):
    if what == "APP":
        return (None, None)
    db, comment = inject("db", "comment")
    tables = dict(
        MEMBER=db.TblMembers,
        EVENT=db.TblEvents,
        STORY=db.TblEvents,
        PHOTO=db.TblPhotos,
        TERM=db.TblTerms,
        DOC=db.TblDocs,
        DOCSEG=db.TblDocSegments,
        VIDEO=db.TblVideos
    )
    tbl = tables[what]
    if what == "EVENT" or what == "TERM":
        rec = db(tbl.story_id==item_id).select().first()
        if rec:
            item_id = rec.id
            story_id = item_id
        else:
            comment(f"rec {item_id} of {what} not found")
            story_id = item_id
    else:
        rec = db(tbl.id==item_id).select().first()
        if rec:
            story_id = rec.story_id
        else:
            story_id = None
            comment(f"rec {item_id} of {what} not found")
    return (story_id, item_id)
    
def fix_hit_records():
    add_missing_bios()
    add_story_id_to_hits()
