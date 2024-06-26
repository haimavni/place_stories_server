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
    q = db.TblMembers.story_id==None
    for member_rec in db(q).select():
        attach_bio_to_member(member_rec)
        
def new_article_story(name):
    STORY4ARTICLE = inject("STORY4ARTICLE")
    sm = stories_manager.Stories()
    story_info = sm.get_empty_story(used_for=STORY4ARTICLE, story_text="", name=name)
    result = sm.add_story(story_info)
    return result.story_id

def attach_story_to_article(article_rec):
    if article_rec.story_id:
        return
    name = article_rec.name.strip()
    story_id = new_article_story(name)
    article_rec.update_record(story_id=story_id)
    
def add_missing_article_stories():
    db = inject("db")
    q = db.TblArticles.story_id==None
    for article_rec in db(q).select():
        attach_story_to_article(article_rec)
        
def add_story_id_to_hits():
    db = inject("db")
    bads = []
    n_goods = 0
    tables = [
        'MEMBER',
        'ARTILE',
        # 'EVENT',
        'PHOTO',
        # 'TERM',
        'DOC',
        'DOCSEG',
        'VIDEO'
    ]
    for what in tables:
        lst = db(((db.TblPageHits.story_id==None) | ((db.TblPageHits.item_id==None))) & (db.TblPageHits.what==what)).select()
        for hit_rec in lst:
            story_id, item_id = calc_hit_story_id(what, hit_rec)
            if story_id:
                n_goods += 1
            else:
                # err = dict(what=what, item_id=hit_rec.item_id, hit_id=hit_rec.id)
                bads.append(hit_rec)
            hit_rec.update_record(story_id=story_id, item_id=item_id)
            
    return dict(bad_hit_records = bads, n_goods = n_goods)
                
def calc_hit_story_id(what, hit_rec):
    if what == "APP":
        return (None, None)
    db, comment = inject("db", "comment")
    tables = dict(
        MEMBER=db.TblMembers,
        ARTICLE=db.TblArticles,
        EVENT=db.TblEvents,
        PHOTO=db.TblPhotos,
        TERM=db.TblTerms,
        DOC=db.TblDocs,
        DOCSEG=db.TblDocSegments,
        VIDEO=db.TblVideos
    )
    tbl = table_of_hit_what(what)
    item_id = hit_rec.item_id
    story_id = hit_rec.story_id
    if what == "EVENT" or what == "TERM":
        n = db(tbl).count()
        if item_id == None:
            rec = db(tbl.story_id == story_id).select().first()
            if not rec:
                return None, story_id
            item_id = rec.id
        elif item_id > n: # item_id is actually story_id
            rec = db(tbl.story_id==item_id).select().first()
            if not rec:
                return None, item_id
            item_id = rec.id
            story_id = item_id
        else:
            rec = db(tbl.id==item_id).select().first()
            if not rec:
                return None, item_id
            story_id = rec.story_id
    else:
        rec = db(tbl.id==item_id).select().first()
        if not rec:
            return None, item_id
        story_id = rec.story_id
    return (story_id, item_id)

def fix_hit_record_stories():
    what = 'EVENT'
    db, STORY4EVENT, STORY4TERM, STORY4MEMBER, STORY4ARTICLE = inject('db', 'STORY4EVENT', 'STORY4TERM', 'STORY4MEMBER', 'STORY4ARTICLE')
    # n_bad_hits = db((db.TblPageHits.item_id==0) and (db.TblPageHits.what!="APP")).delete()
    hits = db((db.TblPageHits.what==what)&(db.TblPageHits.story_id==None)&(db.TblPageHits.date!=None)).select(orderby=~db.TblPageHits.id)

    bad = []
    total_miss = []
    for hit in hits:
        event = db(db.TblEvents.story_id==hit.item_id).select().first()
        if event:
            hit.update_record(story_id=event.story_id, item_id=event.id)
        else:
            story = db(db.TblStories.id==hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
            bad += [dict(hit=hit, story=story)]
            event = db(db.TblEvents.id==hit.item_id).select().first()
            if event:
                hit.update_record(story_id=event.story_id)
            else:
                total_miss += [hit]

    dfukim = []
    for hit in total_miss:
        story = db(db.TblStories.id==hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
        dfukim += [story]

    not_stories = []
    missing = []
    found_events = []
    old_hits = db((db.TblPageHits.what==what)&(db.TblPageHits.story_id==None)&(db.TblPageHits.date==None)).select(orderby=~db.TblPageHits.id)
    for hit in old_hits:
        event = db(db.TblEvents.story_id==hit.item_id).select().first()
        if event:
            item_id = hit.item_id
            found_events += [hit]
            hit.update_record(story_id=item_id, item_id=event.id)
            continue
        story = db(db.TblStories.id==hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
        if not story:
            missing += [hit]
        # elif story.used_for!=STORY4EVENT:
        #     not_stories += [dict(hit=hit, story=story)]
        #     if story.used_for==STORY4MEMBER:
        #         member = db(db.TblMembers.story_id == hit.item_id).select().first()
        #         if member:
        #             hit.update_record(what="MEMBER", item_id=member.id, story_id=hit.item_id)
        #     elif story.used_for==STORY4ARTICLE:
        #         article = db(db.TblArtcles.story_id == hit.item_id).select().first()
        #         if article:
        #             hit.update_record(what="ARTICLE", item_id=article.id, story_id=hit.item_id)
        #     elif story.used_for==STORY4TERM:
        #         term = db(db.TblTerms.story_id==hit.item_id).select().first()
        #         if term:
        #             hit.update_record(what="TERM", story_id=hit.item_id, item_id=term.id) 
    return dict(bad=bad, total_miss=total_miss, dfukim=dfukim, missing=missing, not_stories=not_stories)

    
def fix_hit_records():
    add_missing_bios()
    fix_hit_record_stories()
    # add_story_id_to_hits()
    
    
   
def check_hit_matches_story_usage(what, to_fix=False):
    db, STORY4MEMBER, STORY4ARTICLE, STORY4EVENT, STORY4TERM, STORY4PHOTO, STORY4DOC, STORY4DOCSEGMENT, DOC4VIDEO = inject( 
        'db', 'STORY4MEMBER', 'STORY4ARTICLE', 'STORY4EVENT', 'STORY4TERM', 'STORY4PHOTO', 'STORY4DOC', 'STORY4DOCSEGMENT', 'STORY4VIDEO')
    usage_of_hit_what = dict(
        MEMBER=STORY4MEMBER,
        ARTICLE=STORY4ARTICLE,
        EVENT=STORY4EVENT,
        TERM=STORY4TERM,
        PHOTO=STORY4PHOTO,
        DOC=STORY4DOC,
        DOCSEG=STORY4DOCSEGMENT,
        VIDEO=DOC4VIDEO
    )
    what_of_usage = dict()
    for w in usage_of_hit_what:
        what_of_usage[usage_of_hit_what[w]] = w
    usage = usage_of_hit_what[what]
    missing = []
    mismatch = []
    hits = db((db.TblPageHits.what==what)&(db.TblPageHits.story_id!=None)).select()
    for hit in hits:
        story = db(db.TblStories.id==hit.story_id).select(db.TblStories.name, db.TblStories.used_for).first()
        if story:
            if story.used_for != usage:
                mismatch += [hit]
                if to_fix:
                    w = what_of_usage[story.used_for]
                    tbl = table_of_hit_what(w)
                    rec = db(tbl.story_id==hit.story_id).select().first()
                    if rec:
                        item_id = rec.id
                    else:
                        item_id = None
                    hit.update_record(what=w, item_id=item_id)
        else:
            missing += [hit]
    return dict(missing=missing, mismatch=mismatch)

def all_hit_mismatches(to_fix=False):
    result = dict()
    for what in ['MEMBER', 'ARTICLE', 'EVENT', 'TERM', 'PHOTO', 'DOC', 'DOCSEG', 'VIDEO']:
       tmp = check_hit_matches_story_usage(what, to_fix=to_fix)
       result[what] = tmp
    return result
       
       
def table_of_hit_what(what):
    db = inject("db")
    tables = dict(
        MEMBER=db.TblMembers,
        ARTICLE=db.TblArticles,
        EVENT=db.TblEvents,
        PHOTO=db.TblPhotos,
        TERM=db.TblTerms,
        DOC=db.TblDocs,
        DOCSEG=db.TblDocSegments,
        VIDEO=db.TblVideos
    )
    return tables[what]
    