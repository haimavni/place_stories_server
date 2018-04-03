import stories_manager
from gluon.storage import Storage
from gluon.utils import web2py_uuid
from my_cache import Cache
import ws_messaging
from http_utils import json_to_storage
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates
import datetime
import os
from dal_utils import insert_or_update
from photos import get_slides_from_photo_list, photos_folder, local_photos_folder, images_folder, crop, save_uploaded_photo
import random
import zlib
import re
from langs import language_name
from words import calc_used_languages, read_words_index, get_all_story_previews, get_reisha
from html_utils import clean_html
from members_support import *
from family_connections import *

@serve_json
def member_list(vars):
    return dict(member_list=get_member_names())

@serve_json
def create_parent(vars):
    gender = vars.gender
    child_name = vars.child_name
    what = 'Pa ' if gender == 'M' else 'Ma '
    rec = new_member_rec(gender=gender, first_name=what + child_name)
    rec.member_info.id = parent_id
    rec.member_info.updater_id = auth.current_user()
    rec.member_info.update_time = datetime.datetime.now()
    rec.member_info.approved = auth.has_membership(DATA_AUDITOR)
    parent_id = db.TblMembers.insert(**rec.member_info)
    
    return dict(member_id=parent_id, member=rec)

def new_member_rec(gender=None, first_name=""):
    new_member = Storage(
        member_info=Storage(
            first_name=first_name,
            last_name="",
            former_first_name="",
            former_last_name="",
            visibility=VIS_NOT_READY,
            date_of_death_dateunit='N',
            date_of_death=Storage(
                date='',
                span=0
            ),
            date_of_birth_dateunit='N',
            date_of_birth=Storage(
                date='',
                span=0
            ),
            gender=gender),
        story_info = Storage(display_version='New Story', story_versions=[], story_text='', story_id=None),
        family_connections =  Storage(
            parents=dict(pa=None, ma=None),
            siblings=[],
            spouses=[],
            children=[]
            ),
        slides=[],
        spouses=[],
        member_stories = [],
        facePhotoURL = 'dummy_face.png',
        name=first_name
    )
    return new_member

@serve_json
def get_member_details(vars):
    if not vars.member_id:
        raise User_Error(T('Member does not exist yet!'))
    if vars.member_id == "new":
        rec = new_member_rec()
        rec.member_info.full_name="members.new-member"
        return rec
    mem_id = int(vars.member_id)
    if vars.what == 'story': #access member via its life story id
        rec = db(db.TblMembers.story_id==mem_id).select().first()
        if rec:
            mem_id = rec.id
        else:
            raise Exception('No member for this story')
    if vars.shift == 'next':
        mem_id += 1
    elif vars.shift == 'prev':
        mem_id -= 1
    member_stories = get_member_stories(mem_id)
    member_info = get_member_rec(mem_id)
    if not member_info:
        raise User_Error('No one there')
    sm = stories_manager.Stories()
    story_info = sm.get_story(member_info.story_id) or Storage(display_version='New Story', topic="member.life-summary", story_versions=[], story_text='', story_id=None)
    story_info.used_for = STORY4MEMBER
    family_connections = get_family_connections(member_info.id)
    slides = get_member_slides(mem_id)
    if member_info.gender == 'F':
        spouses = 'husband' + ('s' if len(family_connections.spouses) > 1 else '')
    else:
        spouses = 'wife' + ('s' if len(family_connections.spouses) > 1 else '')
    member_stories = [story_info] + member_stories;
    return dict(member_info=member_info, 
                story_info=story_info, 
                family_connections=family_connections, 
                slides=slides, #todo: duplicate?
                spouses=spouses, #this is just the key for translation
                member_stories=member_stories,
                facePhotoURL = photos_folder('profile_photos') + (member_info.facePhotoURL or "dummy_face.png")
                )

@serve_json
def get_all_relatives(vars):
    member_id = vars.member_id;
    fc = get_all_family_connections(member_id);
    levels = fc.levels
    relative_list = []
    for level in levels:
        lst = [mid for mid in level]
        relative_list.append(lst)
    return dict(relative_list=relative_list)

@serve_json
def get_relatives_path(vars):
    origin_member_id = vars.origin_member_id
    other_member_id = vars.other_member_id
    fc = get_all_family_connections(origin_member_id);
    path = fc.find_path(other_member_id)
    return dict(relatives_path=[origin_member_id] + path)

@serve_json
def get_member_photo_list(vars):
    if vars.member_id == "new":
        return dict(photo_list=[])
    member_id = int(vars.member_id)
    if vars.what == 'story':
        rec = db(db.TblMembers.story_id==member_id).select().first()
        if rec:
            member_id = rec.id
        else:
            return []
    slides = get_member_slides(member_id)
    return dict(photo_list=slides)

@serve_json
def add_photographer(vars):
    photographer_name = vars.photographer_name
    if not db(db.TblPhotographers.name==photographer_name).isempty():
        raise User_Error("photos.already-exists")
    db.TblPhotographers.insert(name=photographer_name)
    ws_messaging.send_message(key='PHOTOGRAPHER_ADDED', group='ALL', photographer_name=photographer_name)
    return dict()
    
@serve_json
def save_story_info(vars):
    user_id = vars.user_id
    story_info = vars.story_info
    info = save_story_data(story_info, user_id=user_id)
    return dict(info=info)

@serve_json
def get_stories_index(vars):
    words_index = read_words_index()
    return dict(stories_index=words_index)

@serve_json
def get_random_member(vars):
    lst = get_members_stats()
    if not lst:
        return dict(member_data = None)
    lst = sorted(lst, key=lambda rec: -rec.num_photos)
    idx = random.randint(0, len(lst) / 5)
    member_data=get_member_rec(lst[idx].member_id)
    member_data.face_photo_url = photos_folder('profile_photos') + member_data.facePhotoURL
    return dict(member_data=member_data)

def get_members_stats():
    q = (db.TblMembers.id == db.TblMemberPhotos.Member_id) & \
        (db.TblMembers.facePhotoURL != None) & (db.TblMembers.facePhotoURL != '')
        ##(db.TblMembers.id == db.TblEventMembers.Member_id)
    lst = db(q).select(db.TblMembers.id, db.TblMembers.id.count(), groupby=[db.TblMembers.id])
    lst = [Storage(member_id=rec.TblMembers.id, num_photos=rec._extra['COUNT(TblMembers.id)']) for rec in lst]
    return lst

@serve_json
def get_stories_sample(vars):
    q = (db.TblStories.used_for==STORY4EVENT) & (db.TblStories.deleted==False)
    q1 = q & (db.TblStories.touch_time != NO_DATE)
    lst1 = db(q1).select(limitby=(0, 10), orderby=~db.TblStories.touch_time)
    lst1 = [rec for rec in lst1]
    q2 = q & (db.TblStories.touch_time == NO_DATE)
    lst2 = db(q2).select(limitby=(0, 200), orderby=~db.TblStories.story_len)
    lst2 = [rec for rec in lst2]
    if len(lst2) > 10:
        lst2 = random.sample(lst2, 10)
    return dict(stories_sample=lst1 + lst2)

def calc_user_list():
    lst = db(db.auth_user).select()
    dic = dict()
    for rec in lst:
        dic[rec.id] = rec
    return dic

@serve_json
def get_story_list(vars):
    MAX_STORIES = 20
    story_topics = get_story_topics()
    params = vars.params

    selected_topics = params.selected_topics or []
    grouped_selected_topics = params.grouped_selected_topics or []
    if selected_topics or grouped_selected_topics:
        lst = get_story_list_with_topics(params, grouped_selected_topics, selected_topics)
    else:
        q = make_stories_query(params)
        lst = db(q).select(limitby=(0, 1000), orderby=~db.TblStories.story_len)
    if len(lst) > 100:
        lst1 = random.sample(lst, 100)
    else:
        lst1 = lst
    ##lst = []
    user_list = calc_user_list()
    if params.checked_story_list:
        checked_story_list = db(db.TblStories.id.belongs(params.checked_story_list)).select()
        checked_story_list = [rec for rec in checked_story_list]
        for rec in checked_story_list:
            rec.checked = True
            if not rec.source:
                rec.author = ''
    else:
        checked_story_list = []
    lst = checked_story_list
    for rec in lst1:
        if 'TblStories' in rec:
            r = rec.TblStories
        else:
            r = rec
        if r.id in params.checked_story_list:
            continue
        if r.author_id:
            user = user_list[r.author_id]
            r.author = user.first_name + ' ' + user.last_name
        else:
            r.author = ""
        r.checked = False
        lst.append(r)
    result = [dict(story_text=rec.story,
                   story_preview=get_reisha(rec.story),
                   name=rec.name, 
                   story_id=rec.id,
                   topics = '; '.join(story_topics[rec.id]) if rec.id in story_topics else "",
                   used_for=rec.used_for,
                   event_date=rec.creation_date, 
                   timestamp=rec.last_update_date,
                   checked=rec.checked,
                   author=rec.source or rec.author) for rec in lst]
    return dict(story_list=result)

@serve_json
def get_story_previews(vars):
    lst = get_all_story_previews()
    return dict(story_previews=license)

@serve_json
def get_story_detail(vars):
    story_id = vars.story_id
    sm = stories_manager.Stories()
    used_for = int(vars.used_for) if vars.used_for and vars.used_for != 'undefined' else STORY4EVENT
    if story_id == 'new':
        story = sm.get_empty_story(used_for=used_for)
        return dict(story=story, members=[], photos=[])
    story_id = int(story_id)
    story=sm.get_story(story_id)
    member_fields = [db.TblMembers.id, db.TblMembers.first_name, db.TblMembers.last_name, db.TblMembers.facePhotoURL]
    members = []
    photos = []
    if story.used_for == STORY4EVENT:
        event = db(db.TblEvents.story_id==story_id).select().first()
        if event:
            qp = (db.TblEventPhotos.Event_id==event.id) & (db.TblPhotos.id==db.TblEventPhotos.Photo_id)
            photos = db(qp).select(db.TblPhotos.id, db.TblPhotos.photo_path)
            photo_ids = [photo.id for photo in photos]
            photo_member_set = photo_lst_member_ids(photo_ids)
            
            photos = [p.as_dict() for p in photos]
            for p in photos:
                p['photo_path'] = photos_folder() + p['photo_path']
            qm = (db.TblEventMembers.Event_id==event.id) & (db.TblMembers.id==db.TblEventMembers.Member_id)
            members = db(qm).select(*member_fields)
            members = [m for m in members]
            member_set = set([m.id for m in members])
            added_members_from_photos = photo_member_set - member_set
            added_members_lst = [mid for mid in added_members_from_photos]
            added_members = db(db.TblMembers.id.belongs(added_members_lst)).select(*member_fields)
            added_members = [m for m in added_members]
            members += added_members
            members = [m.as_dict() for m in members]
            for m in members:
                m['full_name'] = m['first_name'] + ' ' + m['last_name']
                if not m['facePhotoURL']:
                    m['facePhotoURL'] = "dummy_face.png"
                m['facePhotoURL'] = photos_folder("profile_photos") + m['facePhotoURL']
    
        #photos = [dict(photo_id=p.id, photo_path=photos_folder()+p.photo_path) for p in photos]
    return dict(story=story, members=members, photos=photos)

def photo_member_ids(photo_id):
    qmp = (db.TblMemberPhotos.Photo_id==photo_id)
    lst = db(qmp).select(db.TblMemberPhotos.Member_id)
    return [mp.Member_id for mp in lst]

def photo_lst_member_ids(photo_id_lst):
    result = set([])
    for photo_id in photo_id_lst:
        member_ids = photo_member_ids(photo_id)
        result |= set(member_ids)
    return result
    
@serve_json
def get_story_photo_list(vars):
    story_id = vars.story_id
    if story_id == 'new':
        return dict(photo_list=[])
    story_id = int(story_id)
    event = db(db.TblEvents.story_id==story_id).select().first()
    if not event:
        return dict(photo_list=[])
    qp = (db.TblEventPhotos.Event_id==event.id) & (db.TblPhotos.id==db.TblEventPhotos.Photo_id)
    photos = get_slides_from_photo_list(qp)
    return dict(photo_list=photos)

@serve_json
def save_member_info(vars):
    user_id = vars.user_id
    member_id = vars.member_id
    member_info = vars.member_info
    if 'facePhotoURL' in member_info:
        del member_info.facePhotoURL #it is saved separately, not updated in client and can only destroy here
    if member_info:
        new_member = not member_info.id
        ##--------------handle dates - new version------------------
        tbl = db.TblMembers
        for fld in tbl:
            if fld.type=='date':
                fld_name = fld.name
                if fld_name + '_dateunit' not in member_info:
                    continue
                unit, date = parse_date(member_info[fld_name].date)
                member_info[fld_name] = date
                member_info[fld_name + '_dateunit'] = unit
                    
        ##--------------handle dates - end--------------------------
        member_info.update_time = datetime.datetime.now()
        member_info.updater_id = vars.user_id
        member_info.approved = auth.has_membership(DATA_AUDITOR, user_id=vars.user_id)
        result = insert_or_update(db.TblMembers, **member_info)
        if isinstance(result, dict):
            return dict(errors=result['errors'])
        member_id = result
        member_rec = get_member_rec(member_id)
        if new_member:
            member_rec.facePhotoURL = photos_folder('profile_photos') + "dummy_face.png"
        member_rec = json_to_storage(member_rec)
        ws_messaging.send_message(key='MEMBER_LISTS_CHANGED', group='ALL', member_rec=member_rec, new_member=new_member)
    result = Storage(info=member_info)
    if member_id:
        result.member_id = member_id;
    #todo: read-modify-write below?
    ##get_member_names() #todo: needed if we use caching again
    return result

@serve_json
def set_member_story_id(vars):
    db(db.TblMembers.id==vars.member_id).update(story_id=vars.story_id)
    sm = stories_manager.Stories()
    sm.set_used_for(vars.story_id, STORY4MEMBER)
    return dict()

@serve_json
def upload_photos(vars):
    uploaded_photo_ids = []
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded files")
    number_uploaded = 0
    number_duplicates = 0
    failed = []
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    for fn in vars:
        if fn.startswith('user'):
            continue
        fil = vars[fn]
        result = save_uploaded_photo(fil.name, fil.BINvalue, user_id)
        if result == 'duplicate':
            number_duplicates += 1
            continue
        if result == 'failed':
            failed.append(fil.name)
            continue
        number_uploaded += 1
        uploaded_photo_ids += [result]
    ws_messaging.send_message(key='PHOTOS_WERE_UPLOADED', group='ALL', uploaded_photo_ids=uploaded_photo_ids)
    return dict(number_uploaded=number_uploaded, number_duplicates=number_duplicates, failed=failed)

@serve_json
def get_photo_detail(vars):
    photo_id = int(vars.photo_id)
    if vars.what == 'story': #This photo is identified by the associated story
        rec = db(db.TblPhotos.story_id==photo_id).select().first()
    else:
        rec = db(db.TblPhotos.id==photo_id).select().first()
    sm = stories_manager.Stories()
    story=sm.get_story(rec.story_id)
    if not story:
        story = sm.get_empty_story(used_for=STORY4PHOTO)
    all_dates = get_all_dates(rec)        
    return dict(photo_src=photos_folder() + rec.photo_path,
                photo_name=rec.Name,
                height=rec.height,
                width=rec.width,
                photo_story=story,
                photo_date_str = all_dates.photo_date.date,
                photo_date_datespan = all_dates.photo_date.span,
                photo_id=rec.id)

@serve_json
def update_photo_caption(vars):
    photo_id = int(vars.photo_id)
    caption = vars.caption
    db(db.TblPhotos.id==photo_id).update(Name=caption)
    return dict()

@serve_json
def update_photo_date(vars):
    photo_date_str = vars.photo_date_str
    photo_dates_info = dict(
        photo_date = (vars.photo_date_str, int(vars.photo_date_datespan))
    )
    rec = db(db.TblPhotos.id==int(vars.photo_id)).select().first()
    update_record_dates(rec, photo_dates_info)
    #todo: save in db
    return dict()

@serve_json
def get_photo_info(vars):
    photo_id = int(vars.photo_id)
    rec = db(db.TblPhotos.id==photo_id).select().first()
    all_dates = get_all_dates(rec)
    if rec.photographer_id:
        photographer_rec = db(db.TblPhotographers.id==rec.photographer_id).select().first()
    else:
        photographer_rec = Storage()
    result = dict(
        name=rec.Name,
        description=rec.Description,
        photographer=photographer_rec.name,
        photo_date_str = all_dates.photo_date.date,
        photo_date_datespan = all_dates.photo_date.span,
        photo_date_dateunit = all_dates.photo_date.unit
    )
    return result

@serve_json
def save_photo_info(vars):
    pi = vars.photo_info
    ###pi.photographer_id = find_or_insert(pi.photographer)
    unit, date = parse_date(pi.photo_date_str)
    del pi.photo_date_str
    pi.photo_date = date
    pi.photo_date_dateunit = unit
    del pi.photographer
    pi.Name = pi.name
    del pi.name
    db(db.TblPhotos.id==vars.photo_id).update(**pi)
    return dict()

def get_member_names():
    q = (db.TblMembers.deleted != True)
    lst = db(q).select()
    arr = [Storage(id=rec.id,
                   name=member_display_name(rec, full=True),
                   title='<span dir="rtl">' + member_display_name(rec, full=True) + '</span>',
                   first_name=rec.first_name,
                   last_name=rec.last_name,
                   former_first_name=rec.former_first_name,
                   former_last_name=rec.former_last_name,
                   nick_name=rec.NickName,
                   gender=rec.gender,
                   birth_date=rec.date_of_birth,
                   visibility=rec.visibility,
                   approved=rec.approved,
                   has_profile_photo=bool(rec.facePhotoURL), #used in client!
                   rnd=random.randint(0, 1000000),
                   facePhotoURL=photos_folder('profile_photos') + (rec.facePhotoURL or "dummy_face.png")) for rec in lst]
    arr.sort(key=lambda item: item.rnd)
    return arr

@serve_json
def remove_member(vars):
    member_id = int(vars.member_id)
    deleted = db(db.TblMembers.id==member_id).update(deleted=True) == 1
    if deleted:
        ws_messaging.send_message(key='MEMBER_DELETED', group='ALL', member_id=member_id)
    return dict(deleted=deleted)

def image_url(rec):
    #for development need full http address
    return photos_folder() + rec.TblPhotos.photo_path

def get_member_slides(member_id):
    q = (db.TblMemberPhotos.Member_id==member_id) & \
        (db.TblPhotos.id==db.TblMemberPhotos.Photo_id)
    return get_slides_from_photo_list(q)

@serve_json
def get_faces(vars):
    photo_id = vars.photo_id;
    lst = db(db.TblMemberPhotos.Photo_id==photo_id).select()
    faces = []
    candidates = []
    for rec in lst:
        if rec.r == None: #found old record which has a member but no location
            if not rec.Member_id:
                db(db.TblMemberPhotos.id==rec.id).delete()
                continue
            name = member_display_name(member_id=rec.Member_id)
            candidate = dict(member_id=rec.Member_id, name=name)
            candidates.append(candidate)
        else:
            face = Storage(x = rec.x, y=rec.y, r=rec.r or 20, photo_id=rec.Photo_id)
            if rec.Member_id:
                face.member_id = rec.Member_id
                face.name = member_display_name(member_id=rec.Member_id)
            faces.append(face)
    face_ids = set([face.member_id for face in faces])
    candidates = [c for c in candidates if not c['member_id'] in face_ids]
    return dict(faces=faces, candidates=candidates)

@serve_json
def save_face(vars):
    face = vars.face    
    assert(face.member_id > 0)
    if vars.make_profile_photo:
        face_photo_url = save_profile_photo(face)
    else:
        face_photo_url = None
    q = (db.TblMemberPhotos.Photo_id==face.photo_id) & \
        (db.TblMemberPhotos.Member_id==face.member_id)
    data = dict(
        Photo_id=face.photo_id,
        Member_id=face.member_id,
        r=face.r,
        x=face.x,
        y=face.y
    )
    rec = db(q).select().first()
    if rec:
        rec.update_record(**data)
    else:
        db.TblMemberPhotos.insert(**data) 
    member_name = member_display_name(member_id=face.member_id)
    return dict(member_name=member_name, face_photo_url=face_photo_url)

@serve_json
def detach_photo_from_member(vars):
    member_id = vars.member_id
    photo_id = vars.photo_id
    q = (db.TblMemberPhotos.Photo_id==photo_id) & \
        (db.TblMemberPhotos.Member_id==member_id)
    good = db(q).delete() == 1
    return dict(photo_detached=good)

def get_photo_list_with_topics(vars):
    first = True
    grouped_selected_topics = vars.grouped_selected_topics or []
    topic_groups = [[t.id for t in topic_group] for topic_group in grouped_selected_topics]
    for topic in vars.selected_topics:
        topic_groups.append([topic.id])
    for topic_group in topic_groups:
        q = make_photos_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblPhotos.id) & (db.TblItemTopics.item_type.like('%P%'))
        ##topic_ids = [t.id for t in topic_group]
        q &= (db.TblItemTopics.topic_id.belongs(topic_group))
        lst = db(q).select()
        lst = [rec.TblPhotos for rec in lst]
        bag1 = set(r.id for r in lst)
        if first:
            first = False
            bag = bag1
        else:
            bag &= bag1
    dic = {}
    for r in lst:
        dic[r.id] = r
    result = [dic[id] for id in bag]
    return result

def make_photos_query(vars):
    q = (db.TblPhotos.width > 0)
    first_year = vars.first_year
    last_year = vars.last_year
    if vars.base_year: #time range may be defined
        if first_year < vars.base_year + 4:
            first_year = 0
        if last_year and last_year > vars.base_year + vars.num_years  - 5:
            last_year = 0
    else:
        first_year = 0
        last_year = 0
    photographer_list = [p.id for p in vars.selected_photographers] if vars.selected_photographers else []
    if len(photographer_list) > 0:
        q &= db.TblPhotos.photographer_id.belongs(photographer_list)
    if first_year:
        from_date = datetime.date(year=first_year, month=1, day=1)
        q &= (db.TblPhotos.photo_date >= from_date)
    if last_year:
        to_date = datetime.date(year=last_year, month=1, day=1)
        q &= (db.TblPhotos.photo_date < to_date)
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblPhotos.upload_date >= upload_date)
    opt = vars.selected_uploader
    if opt == 'mine':
        q &= (db.TblPhotos.uploader==vars.user_id)
    elif opt == 'users':
        q &= (db.TblPhotos.uploader!=None)
    opt = vars.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblPhotos.photo_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblPhotos.photo_date == NO_DATE)
    return q

@serve_json
def get_photo_list(vars):
    selected_topics = vars.selected_topics or []
    grouped_selected_topics = vars.grouped_selected_topics or []
    privileges = auth.get_privileges()
    mprl = vars.max_photos_per_line or 8;
    MAX_PHOTOS_COUNT = 100 + (mprl - 8) * 100
    if selected_topics or grouped_selected_topics:
        lst = get_photo_list_with_topics(vars)
    else:
        q = make_photos_query(vars)
        n = db(q).count()
        if n > MAX_PHOTOS_COUNT:
            frac = max(MAX_PHOTOS_COUNT * 100 / n, 1)
            sample = random.sample(range(1, 101), frac)
            ##q &= (db.TblPhotos.random_photo_key <= frac)
            q &= (db.TblPhotos.random_photo_key.belongs(sample)) #we don't want to bore our uses so there are several collections
        lst = db(q).select() ###, db.TblPhotographers.id) ##, db.TblPhotographers.id)
    if len(lst) > MAX_PHOTOS_COUNT:
        lst1 = random.sample(lst, MAX_PHOTOS_COUNT)
        lst = lst1
    selected_photo_list = vars.selected_photo_list
    result = []
    if selected_photo_list:
        lst1 = db(db.TblPhotos.id.belongs(selected_photo_list)).select()
        lst1 = [rec for rec in lst1]
        for rec in lst1:
            rec.selected = 'photo-selected'
    else:
        lst1 = []
    lst1_ids = [rec.id for rec in lst1]
    lst = [rec for rec in lst if rec.id not in lst1_ids]
    lst = lst1 + lst
    for rec in lst:
        dic = dict(
            keywords = rec.KeyWords or "",
            description = rec.Description or "",
            name = rec.Name,
            title='{}: {}'.format(rec.Name, rec.KeyWords),
            square_src = photos_folder('squares') + rec.photo_path,
            src=photos_folder('orig') + rec.photo_path,
            photo_id=rec.id,
            width=rec.width,
            height=rec.height,
            selected=rec.selected if 'selected' in rec else ''
        )
        result.append(dic)
    return dict(photo_list=result)

@serve_json
def get_topic_list(vars):
    if vars.usage:
        usage = vars.usage
    elif vars.params:
        usage = ""
        topic_chars = 'xMEPTV'
        story_types = vars.params.selected_story_types
        story_types = [st.id for st in story_types]
        for t in story_types:
            usage += topic_chars[t] 
    else:
        usage = ""
    q = db.TblTopics.id > 0
    if usage:
        q1 = None
        for c in usage:
            if q1:
                q1 |= (db.TblTopics.usage.like("%" + c + "%"))
            else:
                q1 = (db.TblTopics.usage.like("%" + c + "%"))
        q &= q1
    topic_list = db(q).select(orderby=db.TblTopics.name)
    topic_list = [dict(name=rec.name, id=rec.id) for rec in topic_list if rec.name]
    photographer_list = db(db.TblPhotographers).select(orderby=db.TblPhotographers.name)
    photographer_list = [dict(name=rec.name, id=rec.id) for rec in photographer_list if rec.name]
    return dict(topic_list=topic_list, photographer_list=photographer_list)

@serve_json
def get_message_list(vars):
    q = (db.TblStories.used_for==STORY4MESSAGE) & (db.TblStories.author_id==db.auth_user.id) & (db.TblStories.deleted != True)
    lst = db(q).select(orderby=~db.TblStories.last_update_date, limitby=(0, vars.limit or 100))
    result = [dict(story_text=rec.TblStories.story, 
                   name=rec.TblStories.name, 
                   story_id=rec.TblStories.id, 
                   timestamp=rec.TblStories.last_update_date, 
                   author=rec.auth_user.first_name + ' ' + rec.auth_user.last_name) for rec in lst]
    return dict(message_list=result)

@serve_json
def get_constants(vars):
    return dict(
        story_type=dict(
            STORY4MEMBER=STORY4MEMBER,
            STORY4EVENT=STORY4EVENT,
            STORY4PHOTO=STORY4PHOTO,
            STORY4TERM=STORY4TERM,
            STORY4MESSAGE=STORY4MESSAGE,
            STORY4HELP=STORY4HELP,
            STORY4FEEDBACK=STORY4FEEDBACK
            ),
        visibility=dict(
            VIS_NEVER=VIS_NEVER, #for non existing members such as the child of a childless couple (it just connects the)
            VIS_NOT_READY=VIS_NOT_READY,
            VIS_VISIBLE=VIS_VISIBLE,
            VIS_HIGH=VIS_HIGH          
        ),
        cause_of_death=dict(
            DC_DIED=0,
            DC_FELL=1,
            DC_KILLED=2,
            DC_MURDERED=3
        )
    )    

@serve_json
def get_used_languages(vars):
    return calc_used_languages(vars)

@serve_json
def get_term_list(vars):
    lst = db((db.TblStories.used_for==STORY4TERM) & (db.TblStories.deleted!=True)).select()
    result = [dict(story_text=rec.story,
                   name=rec.name, 
                   story_id=rec.id, 
                   author=rec.source) for rec in lst]
    return dict(term_list=result)

def save_profile_photo(face):
    rec = get_photo_rec(face.photo_id)
    input_path = local_photos_folder() + rec.photo_path
    rnd = random.randint(0, 1000) #if we use the same photo and just modify crop, change is not seen because of caching
    facePhotoURL = "PP-{}-{}-{:03}.jpg".format(face.member_id, face.photo_id, rnd)
    output_path = local_photos_folder("profile_photos") + facePhotoURL
    crop(input_path, output_path, face)
    db(db.TblMembers.id==face.member_id).update(facePhotoURL=facePhotoURL)
    return photos_folder("profile_photos") + facePhotoURL

def get_photo_rec(photo_id):
    rec = db(db.TblPhotos.id==photo_id).select().first()
    return rec

def save_story_data(story_info, user_id):
    story_id = story_info.story_id
    sm = stories_manager.Stories(user_id)
    if story_id:
        result = sm.update_story(story_id, story_info)
    else:
        result = sm.add_story(story_info)
    return result

def get_member_stories(member_id):
    q = (db.TblEventMembers.Member_id==member_id) & \
        (db.TblEventMembers.Event_id==db.TblEvents.id) & \
        (db.TblEvents.story_id==db.TblStories.id) & \
        (db.TblStories.deleted==False)
    result = []
    lst = db(q).select()
    for rec in lst:
        event = rec.TblEvents
        story = rec.TblStories
        dic = dict(
            topic = event.Name,
            name = story.name,
            story_id = story.id,
            story_text = story.story,
            source = event.SSource,
            used_for=story.used_for, 
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date
        )
        result.append(dic)
    return result

def _get_story_topics():
    q = (db.TblItemTopics.story_id==db.TblStories.id) & (db.TblTopics.id==db.TblItemTopics.topic_id)
    dic = dict()
    for rec in db(q).select(db.TblStories.id, db.TblItemTopics.story_id, db.TblTopics.name):
        story_id = rec.TblStories.id
        topic_name = rec.TblTopics.name
        if story_id not in dic:
            dic[story_id] = []
        dic[story_id].append(topic_name)
    return dic

def get_story_topics(refresh=False):
    c = Cache('get_story_topics')
    return c(_get_story_topics, refresh)

def make_stories_query(params):
    getting_live_stories = not params.deleted_stories
    q = (db.TblStories.deleted != getting_live_stories) & (db.TblStories.used_for.belongs(STORY4USER)) 
    selected_story_types = [x.id for x in params.selected_story_types]
    if selected_story_types:
        q &= (db.TblStories.used_for.belongs(selected_story_types))
    selected_stories = params.selected_stories
    if selected_stories:
        q &= (db.TblStories.id.belongs(selected_stories))
    if params.selected_languages:
        langs = [x.id for x in params.selected_languages]
        if langs:
            q &= (db.TblStories.language.belongs(langs))
    if params.link_class == "primary":
        q &= (db.TblStories.story.like("%givat-brenner.co.il%"))
    if params.days_since_update and params.days_since_update.value:
        date0 = datetime.datetime.now() - datetime.timedelta(days=params.days_since_update.value)
        q &= (db.TblStories.last_update_date>date0)
    return q

def get_story_list_with_topics(params, grouped_selected_topics, selected_topics):
    first = True
    grouped_selected_topics = grouped_selected_topics or []
    topic_groups = [[t.id for t in topic_group] for topic_group in grouped_selected_topics]
    for topic in selected_topics:
        topic_groups.append([topic.id])
    for topic_group in topic_groups:
        q = make_stories_query(params) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.story_id==db.TblStories.id)
        q &= (db.TblItemTopics.topic_id.belongs(topic_group))
        lst = db(q).select()
        ###lst = [rec.TblStories for rec in lst]
        bag1 = set(r.TblStories.id for r in lst)
        if first:
            first = False
            bag = bag1
        else:
            bag &= bag1
    dic = dict()
    for r in lst:
        dic[r.TblStories.id] = r
    result = [dic[id] for id in bag]
    return result

def _merge_members(mem1_id, mem2_id):
    photos1 = db(db.TblMemberPhotos.Member_id==mem1_id).select()
    photos2 = db(db.TblMemberPhotos.Member_id==mem2_id).select()
    set1 = set([rec.Photo_id for rec in photos1])
    set2 = set([rec.Photo_id for rec in photos2])
    for rec in photos2:
        if rec.Photo_id in set1:
            db(db.TblMemberPhotos.id==rec.id).delete
        else:
            rec.update_record(Member_id=mem1_id)
    db(db.TblMembers.id==mem2_id).update(deleted=True)
    
def merge_members():
    mem1 = int(request.vars.mem1)
    mem2 = int(request.vars.mem2)
    _merge_members(mem1, mem2)
    return "Members merged"
    
@serve_json    
def get_theme_data(vars):
    path = images_folder()
    files = dict(
        ##content_background='content-background.png',
        header_background='header-background.png',
        top_background='top-background.png',
        footer_background='footer-background.png',
        founders_group_photo='founders_group_photo.jpg',
        gb_logo_png='gb-logo.png',
        himnon='himnon-givat-brenner.mp3',
        content_background='bgs/body-bg.jpg',
        mayflower='bgs/mayflower.jpg'
    )
    result = dict()
    for k in files:
        result[k] = path + files[k]
    return dict(files=result)

@serve_json
def delete_checked_stories(vars):
    params = vars.params
    checked_stories = params.checked_story_list
    deleted = not params.deleted_stories #will undelete if the list is of deleted stories
    n = db(db.TblStories.id.belongs(checked_stories)).update(deleted=deleted)
    return dict(num_deleted=n)

@serve_json
def delete_story(vars):
    story_id = vars.story_id
    n = db(db.TblStories.id==story_id).update(deleted=True)
    return dict(deleted=n==1)
    
@serve_json
def save_tag_merges(vars):
    gst = vars.grouped_selected_topics
    for topic_group in gst:
        topic0 = topic_group[0]
        rec0 = db(db.TblTopics.id==topic0.id).select().first()
        for topic in topic_group[1:]:
            rec = db(db.TblTopics.id==topic.id).select().first()
            if not rec.usage:
                continue
            for c in rec.usage:
                if c not in rec0.usage:
                    rec0.usage += c
                    rec0.update_record(usage=rec0.usage)
                    
            db(db.TblItemTopics.topic_id==rec.id).update(topic_id=rec0.id)
            db(db.TblTopics.id==rec.id).delete()
        
    gsp = vars.grouped_selected_photographers
    for p_group in gsp:
        p0 = p_group[0]
        rec0 = db(db.TblPhotographers.id==p0.id).select().first()
        for p in p_group[1:]:
            rec = db(db.TblPhotographers.id==p.id).select().first()
            db(db.TblPhotos.photographer_id==rec.id).update(photographer_id=rec0.id)
        db(db.TblPhotographers.id==rec.id).delete()
        
    ws_messaging.send_message(key='TAGS_MERGED', group='ALL')
    return dict()
    
@serve_json
def apply_to_selected_photos(vars):
    all_tags = calc_all_tags()
    spl = vars.selected_photo_list
    plist = vars.selected_photographers
    if len(plist) == 1:
        photographer_id = plist[0].id
    else:
        photographer_id = None
    photos_date_str = vars.photos_date_str
    if photos_date_str:
        dates_info = dict(
            photo_date = (photos_date_str, vars.photos_date_span_size)
        )
    else:
        dates_info = None
    
    st = vars.selected_topics
    added = []
    deleted = []
    for pid in spl:
        curr_tag_ids = set(get_tag_ids(pid, "P"))
        for topic in st:
            item = dict(item_id=pid, topic_id=topic.id)
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type="P", item_id=pid, topic_id=topic.id) #todo: story_id=???
                curr_tag_ids |= set([topic.id])
                added.append(item)
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=="P") & (db.TblItemTopics.item_id==pid) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        rec = db(db.TblPhotos.id==pid).select().first()
        rec.update_record(KeyWords=keywords)
        if photographer_id:
            rec.update_record(photographer_id=photographer_id)
        if dates_info:
            update_record_dates(rec, dates_info)
    ws_messaging.send_message('PHOTO-TAGS-CHANGED', added=added, deleted=deleted)
    return dict()

@serve_json
def promote_stories(vars):
    checked_story_list = vars.params.checked_story_list
    q = (db.TblStories.id.belongs(checked_story_list))
    today = datetime.date.today()
    db(q).update(touch_time=today)
 
def calc_all_tags():
    result = dict()
    for rec in db(db.TblTopics).select():
        result [rec.id] = rec.name
    return result
    
@serve_json
def save_group_members(vars):
    if vars.caller_type == 'story':
        return save_story_members(vars.caller_id, vars.member_ids)
    else:
        return dict() #todo: implement for terms etc.
    
@serve_json
def get_video_sample(vars):
    #temporary hard coded implementation
    lst = ['-5F0x79j2K4', 'uwACSZ890a0', 'dfJIOa6eyfg', '1g_PlRE-YwI', '4I7BtUDPfcA', 'Cdiq5As8vCw']
    return dict(video_list=lst)
    
def save_story_members(story_id, member_ids):
    event = db(db.TblEvents.story_id==story_id).select().first()
    qm = (db.TblEventMembers.Event_id==event.id) & (db.TblMembers.id==db.TblEventMembers.Member_id)
    old_members = db(qm).select(db.TblMembers.id)
    old_members = [m.id for m in old_members]
    for m in old_members:
        if m not in member_ids:
            db((db.TblEventMembers.Member_id==m) & (db.TblEventMembers.Event_id==event.id)).delete()
    for m in member_ids:
        if m not in old_members:
            db.TblEventMembers.insert(Member_id=m, Event_id=event.id)
    
    return dict()

@serve_json
def save_photo_group(vars):
    story_id = vars.caller_id
    event = db(db.TblEvents.story_id==story_id).select().first()
    qp = (db.TblEventPhotos.Event_id==event.id) & (db.TblEventPhotos.Photo_id==db.TblPhotos.id)
    old_photos = db(qp).select(db.TblPhotos.id)
    old_photos = [p.id for p in old_photos]
    photo_ids = vars.photo_ids
    for p in old_photos:
        if p not in photo_ids:
            db((db.TblEventPhotos.Photo_id==p) & (db.TblEventPhotos.Event_id==event.id)).delete()
    for p in vars.photo_ids:
        if p not in old_photos:
            db.TblEventPhotos.insert(Photo_id=p, Event_id=event.id)
    return dict()
    
def get_tag_ids(item_id, item_type):
    q = (db.TblItemTopics.item_type==item_type) & (db.TblItemTopics.item_id==item_id)
    lst = db(q).select()
    return [rec.topic_id for rec in lst]

@serve_json
def consolidate_stories(vars):
    lst = vars.stories_to_merge
    lst = [(get_story_name(story_id), story_id) for story_id in lst]
    lst = sorted(lst)
    stm = [item[1] for item in lst]
    base_event_id = event_id_of_story_id(stm[0])
    #--------merge photos-------------------------
    base_photo_ids = set(get_story_photo_ids(stm[0]))
    added_photo_ids = set([])
    for story_id in stm[1:]:
        added_photo_ids |= set(get_story_photo_ids(story_id))
    added_photo_ids = added_photo_ids - base_photo_ids
    for pid in added_photo_ids:
        db.TblEventPhotos.insert(Photo_id=pid, Event_id=base_event_id)
    for pid in added_photo_ids:
        event_id = event_id_of_story_id(pid)
        db((db.TblEventPhotos.Event_id==event_id) & (db.TblEventPhotos.Photo_id==pid)).delete()
    #--------merge members--------------------------
    base_member_ids = set(get_story_member_ids(stm[0]))
    added_member_ids = set([])
    for story_id in stm[1:]:
        added_member_ids |= set(get_story_member_ids(story_id))
    added_member_ids = added_member_ids - base_member_ids
    for pid in added_member_ids:
        db.TblEventMembers.insert(Member_id=pid, Event_id=base_event_id)
    for pid in added_member_ids:
        event_id = event_id_of_story_id(pid)
        db((db.TblEventMembers.Event_id==event_id) & (db.TblEventMembers.Member_id==pid)).delete()
    #--------merge stories--------------------------
    story = get_story_text(stm[0])
    for i, story_id in enumerate(stm[1:]):
        name = lst[i+1][0]
        story += '<br>----------' + name + '-------------------<br>'
        story += get_story_text(story_id)
    db(db.TblStories.id==stm[0]).update(story=story)
    #--------delete obsolete stories----------------
    db(db.TblStories.id.belongs(stm[1:])).update(deleted=True)
    return dict()

@serve_json
def clean_html_format(vars):
    html = vars.html
    html = clean_html(html)
    return dict(html=html)

@serve_json
def count_hit(vars):
    rec = db((db.TblPageHits.what==vars.what)&(db.TblPageHits.item_id==vars.item_id)).select().first()
    if rec:
        rec.update_record(count=rec.count+1)
    else:
        db.TblPageHits.insert(what=vars.what, item_id=vars.item_id, count=1)
    return dict()
    
def get_story_text(story_id):
    rec = db(db.TblStories.id==story_id).select().first()
    if rec:
        return rec.story
    else:
        return ''
    
def get_story_name(story_id):
    rec = db(db.TblStories.id==story_id).select().first()
    if rec:
        return rec.name
    else:
        return ''
    
def event_id_of_story_id(story_id):
    rec = db(db.TblEvents.story_id==story_id).select().first()
    if rec:
        return rec.id
    else:
        return None

def get_story_photo_ids(story_id):
    event_id = event_id_of_story_id(story_id)
    if not event_id:
        return []
    qp = (db.TblEventPhotos.Event_id==event_id) & (db.TblPhotos.id==db.TblEventPhotos.Photo_id)
    lst = db(qp).select(db.TblPhotos.id)
    lst = [p.id for p in lst]
    return lst

def get_story_member_ids(story_id):
    event_id = event_id_of_story_id(story_id)
    if not event_id:
        return []
    qm = (db.TblEventMembers.Event_id==event_id) & (db.TblMembers.id==db.TblEventMembers.Member_id)
    lst = db(qm).select(db.TblMembers.id)
    lst = [m.id for m in lst]
    return lst
