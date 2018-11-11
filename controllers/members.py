import stories_manager
from gluon.storage import Storage
from gluon.utils import web2py_uuid
from my_cache import Cache
import ws_messaging
from http_utils import json_to_storage
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
import datetime
import os
from dal_utils import insert_or_update
from photos import get_slides_from_photo_list, photos_folder, local_photos_folder, images_folder, local_images_folder, crop, save_uploaded_photo, rotate_photo
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
    member_stories = get_member_stories(mem_id) + get_member_terms(mem_id)
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
    lst = lst1 + lst2;
    for r in lst:
        r.story_preview = get_reisha(r.story, 16)
    return dict(stories_sample=lst)

def calc_user_list():
    lst = db(db.auth_user).select()
    dic = dict()
    for rec in lst:
        dic[rec.id] = rec
    return dic

def get_checked_stories(params):
    if params.checked_story_list:
        checked_story_list = db(db.TblStories.id.belongs(params.checked_story_list)).select()
        checked_story_list = [rec for rec in checked_story_list]
        for rec in checked_story_list:
            rec.checked = True
            if not rec.source:
                rec.author = ''
    else:
        checked_story_list = []
    return checked_story_list

def _get_story_list(params, exact, checked):
    ###story_topics = get_story_topics()
    if not query_has_data(params):
        n = db(db.TblStories).count()
        rng = range(1, n+1)
        sample_size = n if n < 100 else 100
        ids = random.sample(rng, sample_size)
        q = (db.TblStories.id.belongs(ids)) & (db.TblStories.deleted != True) & (db.TblStories.used_for.belongs(STORY4USER))
        lst1 = db(q).select()
        checked = False
    elif checked:
        lst1 = get_checked_stories(params)
    else:
        selected_topics = params.selected_topics or []
        if selected_topics:
            lst1 = get_story_list_with_topics(params, selected_topics, exact)
        else:
            q = make_stories_query(params, exact)
            if not q:
                return []
            lst1 = db(q).select(limitby=(0, 1000), orderby=~db.TblStories.story_len)
    user_list = calc_user_list()
    lst = []
    for rec in lst1:
        if 'TblStories' in rec:
            r = rec.TblStories
        else:
            r = rec
        if r.id in params.checked_story_list and not checked:
            continue
        if r.author_id:
            user = user_list[r.author_id]
            r.author = user.first_name + ' ' + user.last_name
        else:
            r.author = ""
        r.checked = checked
        r.search_kind = 'exact' if exact else 'nonexact'
        lst.append(r)
    return lst

@serve_json
def get_story_list(vars):
    CHUNK = 100
    qhd = query_has_data(vars.params)
    result0 = []
    result1 = []
    result2 = []
    if qhd:
        if vars.params.search_type=='advanced':
            result1 = []
        else:
            result1 = _get_story_list(vars.params, exact=True, checked=False) #if keywords_str, only exact matches are returned, otherwise whatever the query gets
        if vars.params.keywords_str or vars.params.search_type=='advanced': #find all pages containing all words in this string
            result2 = _get_story_list(vars.params, exact=False, checked=False)
        else:
            result2 = []
    else:
        result0 = _get_story_list(vars.params, exact=True, checked=True)
    result = result0 + result1 + result2
    result_type_counters = dict()
    active_result_types = set()
    final_result = []
    for story in result: 
        k = story.used_for
        active_result_types |= set([k])
        if k not in result_type_counters:
            result_type_counters[k] = 0
        if result_type_counters[k] >= 100:
            continue
        result_type_counters[k] += 1
        final_result.append(story)
    active_result_types = [k for k in active_result_types]
    active_result_types = sorted(active_result_types)
    result = final_result
    for i in range(0, len(result), CHUNK):
        chunk = result[i:i+CHUNK]
        chunk = set_story_list_data(chunk)
        ws_messaging.send_message(key='STORY-LIST-CHUNK', 
                                  group=vars.ptp_key, 
                                  first=i,
                                  num_stories=len(result),
                                  chunk_size=CHUNK, 
                                  chunk=chunk, 
                                  active_result_types=active_result_types,
                                  result_type_counters=result_type_counters)
    return dict(no_results=len(result)==0)

def set_story_list_data(story_list):
    user_list = auth.user_list()
    result = [Storage(
        story_text=rec.story,
        story_preview=get_reisha(rec.story),
        name=rec.name, 
        story_id=rec.id,
        topics = rec.keywords, ###'; '.join(story_topics[rec.id]) if rec.id in story_topics else "",
        used_for=rec.used_for,
        event_date=rec.creation_date, 
        timestamp=rec.last_update_date,
        updater=user_list[rec.updater_id] if rec.updater_id and rec.updater_id in user_list else dict(),
        checked=rec.checked,
        ##exact=exact and params.search_type != 'advanced',
        author=rec.source or rec.author) for rec in story_list]
    assign_photos(result)
    return result

def assign_photos(story_list):
    photo_story_list = dict()
    video_story_list = dict()
    for story in story_list:
        if story.used_for == STORY4PHOTO:
            photo_story_list[story.story_id] = story
        elif story.used_for == STORY4VIDEO:
            video_story_list[story.story_id] = story
    photo_story_ids = photo_story_list.keys()
    lst = db(db.TblPhotos.story_id.belongs(photo_story_ids)).select(db.TblPhotos.story_id, db.TblPhotos.photo_path)
    for photo in lst:
        photo_src = photos_folder('squares') + photo.photo_path
        photo_story_list[photo.story_id].photo_src = photo_src
    video_story_ids = video_story_list.keys()
    lst = db(db.TblVideos.story_id.belongs(video_story_ids)).select(db.TblVideos.story_id, db.TblVideos.src)
    for video in lst:
        video_story_list[video.story_id].video_src = "//www.youtube.com/embed/" + video.src + "?wmode=opaque"

@serve_json
def get_story_previews(vars):
    lst = get_all_story_previews()
    return dict(story_previews=lst)

@serve_json
def get_story(vars):
    sm = stories_manager.Stories()
    story_id = int(vars.story_id)
    return dict(story=sm.get_story(story_id))

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
    candidates = [] #members found in the attached photos
    photos = []
    if story.used_for == STORY4EVENT:
        event = db(db.TblEvents.story_id==story_id).select().first()
        if event:
            qp = (db.TblEventPhotos.Event_id==event.id) & (db.TblPhotos.id==db.TblEventPhotos.Photo_id) & (db.TblPhotos.deleted != True)
            photos = db(qp).select(db.TblPhotos.id, db.TblPhotos.photo_path)
            photo_ids = [photo.id for photo in photos]
            photo_member_set = photo_lst_member_ids(photo_ids)

            photos = [p.as_dict() for p in photos]
            for p in photos:
                p['photo_path'] = photos_folder() + p['photo_path']
            qm = (db.TblEventMembers.Event_id==event.id) & (db.TblMembers.id==db.TblEventMembers.Member_id) & (db.TblMembers.deleted != True)
            members = db(qm).select(*member_fields)
            members = [m for m in members]
            member_set = set([m.id for m in members])
            added_members_from_photos = photo_member_set - member_set
            added_members_lst = [mid for mid in added_members_from_photos]
            added_members = db(db.TblMembers.id.belongs(added_members_lst)).select(*member_fields)
            candidates = [m.as_dict() for m in added_members]
            members = [m.as_dict() for m in members]
            lst = [members, candidates]
            for arr in lst:
                for m in arr:
                    m['full_name'] = m['first_name'] + ' ' + m['last_name']
                    if not m['facePhotoURL']:
                        m['facePhotoURL'] = "dummy_face.png"
                    m['facePhotoURL'] = photos_folder("profile_photos") + m['facePhotoURL']
    elif story.used_for == STORY4TERM:  #todo: try to consolidate with the above
        term = db(db.TblTerms.story_id==story_id).select().first()
        if term:
            qp = (db.TblTermPhotos.term_id==term.id) & (db.TblPhotos.id==db.TblTermPhotos.Photo_id) & (db.TblPhotos.deleted != True)
            photos = db(qp).select(db.TblPhotos.id, db.TblPhotos.photo_path)
            photo_ids = [photo.id for photo in photos]
            photo_member_set = photo_lst_member_ids(photo_ids)

            photos = [p.as_dict() for p in photos]
            for p in photos:
                p['photo_path'] = photos_folder() + p['photo_path']
            qm = (db.TblTermMembers.term_id==term.id) & (db.TblMembers.id==db.TblTermMembers.Member_id)
            members = db(qm).select(*member_fields)
            members = [m for m in members]
            member_set = set([m.id for m in members])
            added_members_from_photos = photo_member_set - member_set
            added_members_lst = [mid for mid in added_members_from_photos]
            added_members = db(db.TblMembers.id.belongs(added_members_lst)).select(*member_fields)
            candidates = [m.as_dict() for m in added_members]
            members = [m.as_dict() for m in members]
            lst = [members, candidates]
            for arr in lst:
                for m in arr:
                    m['full_name'] = m['first_name'] + ' ' + m['last_name']
                    if not m['facePhotoURL']:
                        m['facePhotoURL'] = "dummy_face.png"
                    m['facePhotoURL'] = photos_folder("profile_photos") + m['facePhotoURL']


        #photos = [dict(photo_id=p.id, photo_path=photos_folder()+p.photo_path) for p in photos]
    return dict(story=story, members=members, candidates=candidates, photos=photos)

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
    if vars.story_type == "story":
        tbl = db.TblEvents
        tbl1 = db.TblEventPhotos
    elif vars.story_type == "term":
        tbl = db.TblTerms
        tbl1 = db.TblTermPhotos
    else:
        raise Exception('Unknown call type in get story photo list')
    item_id = db(tbl.story_id==story_id).select().first().id
    if vars.story_type == "story":
        qp = (db.TblEventPhotos.Event_id==item_id) & (db.TblPhotos.id==db.TblEventPhotos.Photo_id)
    else:
        qp = (db.TblTermPhotos.term_id==item_id) & (db.TblPhotos.id==db.TblTermPhotos.Photo_id)
    qp &= (db.TblPhotos.deleted!=True)
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
        member_info.updater_id = vars.user_id or auth.current_user() or 2
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

serve_json
def upload_photo(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded files")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_photo(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

@serve_json
def notify_new_photos(vars):
    uploaded_photo_ids = vars.uploaded_photo_ids
    ws_messaging.send_message(key='PHOTOS_WERE_UPLOADED', group='ALL', uploaded_photo_ids=uploaded_photo_ids)
    return dict()

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
    photo_rec = db(db.TblPhotos.id==photo_id).select().first()
    photo_rec.update(Name=caption)
    sm = stories_manager.Stories()
    sm.update_story_name(photo_rec.story_id, caption)
    return dict(bla='bla')

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
    photo_rec = db(db.TblPhotos.id==vars.photo_id).select().first()
    if pi.name != photo_rec.Name:
        sm = stories_manager.Stories(vars.user_id)
        sm.update_story_name(photo_rec.story_id, pi.name)
    del pi.photo_date_str
    pi.photo_date = date
    pi.photo_date_dateunit = unit
    del pi.photographer
    pi.Name = pi.name
    del pi.name
    photo_rec.update_record(**pi)
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
        (db.TblPhotos.id==db.TblMemberPhotos.Photo_id) & \
        (db.TblPhotos.deleted!=True)
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
    if vars.old_member_id:
        q = (db.TblMemberPhotos.Photo_id==face.photo_id) & \
            (db.TblMemberPhotos.Member_id==vars.old_member_id)
    else:
        q = None
    data = dict(
        Photo_id=face.photo_id,
        Member_id=face.member_id,
        r=face.r,
        x=face.x,
        y=face.y
    )
    rec = None
    if q:
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

def flatten_option_list(option_list):
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

def get_photo_list_with_topics(vars):
    first = True
    topic_groups = calc_grouped_selected_options(vars.selected_topics)
    for topic_group in topic_groups:
        q = make_photos_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblPhotos.id) & (db.TblItemTopics.item_type.like('%P%'))
        ##topic_ids = [t.id for t in topic_group]
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
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
    q = (db.TblPhotos.width > 0) & (db.TblPhotos.deleted!=True)
    #if vars.relevant_only:
        #q &= (db.TblPhotos.usage > 0)
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
    photographer_list = [p.option.id for p in vars.selected_photographers] if vars.selected_photographers else []
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
    if vars.selected_member_id:
        member_id = vars.selected_member_id
        q1 = (db.TblMemberPhotos.Member_id==member_id) & \
            (db.TblPhotos.id==db.TblMemberPhotos.Photo_id)
        q &= q1
    return q

@serve_json
def get_photo_list(vars):
    selected_topics = vars.selected_topics or []
    mprl = vars.max_photos_per_line or 8;
    MAX_PHOTOS_COUNT = 100 + (mprl - 8) * 100
    if selected_topics:
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
        if lst and 'TblMemberPhotos' in lst[0]:
            lst = [rec.TblPhotos for rec in lst]
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
def get_message_list(vars):
    q = (db.TblStories.used_for==STORY4MESSAGE) & (db.TblStories.author_id==db.auth_user.id) & (db.TblStories.deleted != True)
    lst = db(q).select(orderby=~db.TblStories.creation_date, limitby=(0, vars.limit or 100))
    result = [dict(story_text=rec.TblStories.story,
                   story_preview=rec.TblStories.story, #it is short anyway
                   name=rec.TblStories.name, 
                   story_id=rec.TblStories.id, 
                   timestamp=rec.TblStories.last_update_date, 
                   author=rec.auth_user.first_name + ' ' + rec.auth_user.last_name) for rec in lst]
    return dict(message_list=result)

@serve_json
def push_message_up(vars):
    sid = vars.story_id
    rec = db(db.TblStories.id==sid).select().first()
    now = datetime.datetime.now()
    if rec:
        rec.update_record(creation_date=now, last_update_date=now)
    return dict()

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
            ),
        ptp_key=web2py_uuid()
    )    

@serve_json
def get_used_languages(vars):
    return calc_used_languages(vars)

@serve_json
def get_term_list(vars):
    lst = db((db.TblStories.used_for==STORY4TERM) & \
             (db.TblStories.deleted!=True) & \
             ###(db.TblTerms.deleted!=True) & \
             (db.TblTerms.story_id==db.TblStories.id)).select(orderby=db.TblStories.name)
    result = [dict(story_text=rec.TblStories.story,
                   story_preview=get_reisha(rec.TblStories.story, size=40),
                   name=rec.TblStories.name, 
                   story_id=rec.TblStories.id, 
                   author=rec.TblStories.source,
                   id=rec.TblTerms.id) for rec in lst]
    return dict(term_list=result)

@serve_json
def delete_term(vars):
    rec = db(db.TblTerms.id==int(vars.term_id)).select().first()
    rec.update(deleted=True)
    story_id = rec.story_id
    db(db.TblStories.id==story_id).update(deleted=True)
    return dict()

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
    result.story_preview = get_reisha(story_info.story_text)
    if story_info.used_for == STORY4PHOTO:
        photo_rec = db(db.TblPhotos.story_id==story_info.story_id).select().first();
        photo_rec.update_record(Name=story_info.name)
    ws_messaging.send_message(key='STORY_WAS_SAVED', group='ALL', story_data=result)
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
            story_preview=get_reisha(story.story, 30),
            source = event.SSource,
            used_for=story.used_for, 
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date
        )
        result.append(dic)
    return result

def get_member_terms(member_id):
    q = (db.TblTermMembers.Member_id==member_id) & \
        (db.TblTermMembers.term_id==db.TblTerms.id) & \
        (db.TblTerms.story_id==db.TblStories.id) & \
        (db.TblStories.deleted==False)
    result = []
    lst = db(q).select()
    for rec in lst:
        term = rec.TblTerms
        story = rec.TblStories
        dic = dict(
            topic = term.Name,
            name = story.name,
            story_id = story.id,
            story_text = story.story,
            story_preview=get_reisha(story.story, 30),
            ###source = term.SSource,
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

def query_has_data(params):
    return params.keywords_str or params.selected_stories or (params.days_since_update and params.days_since_update.value) or \
        params.approval_state in [2,3] or params.selected_topics or params.selected_words
        
def make_stories_query(params, exact):
    getting_live_stories = not params.deleted_stories
    q = (db.TblStories.deleted != getting_live_stories) & (db.TblStories.used_for.belongs(STORY4USER)) 
    selected_stories = params.selected_stories
    ##if exact and params.search_type != 'advanced':
        ##return None

    if params.keywords_str:
        selected_stories = [];
        if exact:
            q &= (db.TblStories.name.contains(params.keywords_str)) | (db.TblStories.story.contains(params.keywords_str))
        else:
            keywords = params.keywords_str.split()
            if len(keywords) == 1:
                return None
            for kw in keywords:
                q &= (db.TblStories.name.contains(kw)) | (db.TblStories.story.contains(kw))
            #prevent duplicates:
            q &= (~db.TblStories.name.contains(params.keywords_str)) & \
                (~db.TblStories.story.contains(params.keywords_str))
    if selected_stories:
        q &= (db.TblStories.id.belongs(selected_stories))
    if params.days_since_update and params.days_since_update.value:
        date0 = datetime.datetime.now() - datetime.timedelta(days=params.days_since_update.value)
        q &= (db.TblStories.last_update_date>date0)
    if params.approval_state == 2:
        q &= (db.TblStories.last_version > db.TblStories.approved_version)
    if params.approval_state == 3:
        q &= (db.TblStories.last_version == db.TblStories.approved_version)
    return q

def get_story_list_with_topics(params, selected_topics, exact):
    first = True
    topic_groups = calc_grouped_selected_options(selected_topics)
    dic = dict()
    bag = None
    for topic_group in topic_groups:
        q = make_stories_query(params, exact) #if we do not regenerate it the query becomes accumulated and necessarily fails
        if not q:
            return []
        q &= (db.TblItemTopics.story_id==db.TblStories.id)

        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
        lst = db(q).select()
        ###lst = [rec.TblStories for rec in lst]
        bag1 = set(r.TblStories.id for r in lst)
        if first:
            first = False
            bag = bag1
        else:
            bag &= bag1
        for r in lst:
            dic[r.TblStories.id] = r
    if not bag:
        return []
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
    local_path = local_images_folder()
    files = dict(
        header_background='header-background.png',
        top_background='top-background.png',
        footer_background='footer-background.png',
        founders_group_photo='founders_group_photo.jpg',
        app_logo='app-logo.png',
        himnon='himnon-givat-brenner.mp3',
        content_background='bgs/body-bg.jpg',
        mayflower='bgs/mayflower.jpg'
    )
    result = dict()
    for k in files:
        result[k] = path + files[k] if os.path.exists(local_path + files[k]) else ''
        if not os.path.exists(local_path + files[k]):
            comment("file {} is missing", k)                   
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
def apply_to_selected_photos(vars):
    all_tags = calc_all_tags()
    spl = vars.selected_photo_list
    plist = vars.selected_photographers
    if len(plist) == 1:
        photographer_id = plist[0].option.id
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
        for tpc in st:
            topic = tpc.option
            item = dict(item_id=pid, topic_id=topic.id)
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                rec = db(db.TblPhotos.id==pid).select().first()
                story_id = rec.story_id if rec else None
                new_id = db.TblItemTopics.insert(item_type="P", item_id=pid, topic_id=topic.id, story_id=story_id)
                curr_tag_ids |= set([topic.id])
                added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if 'P' not in topic_rec.usage:
                    usage = topic_rec.usage + 'P'
                    topic_rec.update_record(usage=usage)
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=="P") & (db.TblItemTopics.item_id==pid) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                #should remove 'P' from usage if it was the last one...
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        rec = db(db.TblPhotos.id==pid).select().first()
        rec.update_record(KeyWords=keywords)
        if photographer_id:
            rec.update_record(photographer_id=photographer_id)
            rec1 = db(db.TblPhotographers.id==photographer_id).select().first()
            kind = rec1.kind or ''
            if not 'P' in kind:
                kind += 'P'
                rec1.update_record(kind=kind)
        if dates_info:
            update_record_dates(rec, dates_info)
    ws_messaging.send_message('PHOTO-TAGS-CHANGED', added=added, deleted=deleted)
    return dict()

@serve_json
def apply_topics_to_selected_stories(vars):
    used_for = vars.used_for
    if used_for:
        usage_chars = 'xMEPTxxxV'
        usage_char = usage_chars[used_for]
    all_tags = calc_all_tags()
    params = vars.params
    checked_story_list = params.checked_story_list
    selected_topics = params.selected_topics
    for eid in checked_story_list:
        curr_tag_ids = set(get_tag_ids(eid, usage_char))
        for item in selected_topics:
            topic = item.option
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type=usage_char, story_id=eid, topic_id=topic.id) 
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if usage_char not in topic_rec.usage:
                    usage = topic_rec.usage + usage_char
                    topic_rec.update_record(usage=usage)
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type==usage_char) & (db.TblItemTopics.item_id==eid) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                #should remove usage_char from usage if it was the last one...
                db(q).delete()

        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        rec = db(db.TblStories.id==eid).select().first()
        rec.update_record(keywords=keywords)

    #todo: notify all users?
    return dict()

@serve_json
def promote_stories(vars):
    checked_story_list = vars.params.checked_story_list
    q = (db.TblStories.id.belongs(checked_story_list))
    today = datetime.date.today()
    db(q).update(touch_time=today)
    return dict()

@serve_json
def promote_videos(vars):
    selected_video_list = vars.params.selected_video_list
    q = (db.TblVideos.id.belongs(selected_video_list))
    today = datetime.date.today()
    db(q).update(touch_time=today)
    return dict()

def calc_all_tags():
    result = dict()
    for rec in db(db.TblTopics).select():
        result [rec.id] = rec.name
    return result

@serve_json
def save_group_members(vars):
    return save_story_members(vars.caller_id, vars.caller_type, vars.member_ids)

@serve_json
def get_video_sample(vars):
    q = (db.TblVideos.deleted==False)
    q1 = q & (db.TblVideos.touch_time != NO_DATE)
    lst1 = db(q1).select(limitby=(0, 10), orderby=~db.TblVideos.touch_time)
    lst1 = [rec.src for rec in lst1]
    q2 = q & (db.TblVideos.touch_time == NO_DATE)
    lst2 = db(q2).select(limitby=(0, 200))
    lst2 = [rec.src for rec in lst2]
    if len(lst2) > 10:
        lst2 = random.sample(lst2, 10)
    lst = lst1 + lst2
    return dict(video_list=lst)

@serve_json
def save_video(vars):
    #https://photos.app.goo.gl/TndZ4fgyih57pmzS6 - shared google photos
    user_id = vars.user_id
    params = vars.params
    date_info = dict(video_date=(params.video_date_datestr, params.video_date_datespan))
    if not params.id: #creation, not modification
        pats = dict(
            youtube=r'https://(?:www.youtube.com/watch\?v=|youtu\.be/)(?P<code>[^&]+)',
            vimeo=r'https://vimeo.com/(?P<code>\d+)'
        )
        src = None
        for t in pats:
            pat = pats[t]
            m = re.search(pat, params.src)
            if m:
                src = m.groupdict()['code']
                typ = t
                break
        if not src:
            raise User_Error('!videos.unknown-video-type')
        q = (db.TblVideos.src==src) & (db.TblVideos.video_type==typ) & (db.TblVideos.deleted!=True)
        if db(q).count() > 0:
            raise User_Error('!videos.duplicate')
        sm = stories_manager.Stories()
        story_info = sm.get_empty_story(used_for=STORY4VIDEO, story_text="", name=params.name)
        result = sm.add_story(story_info)
        story_id = result.story_id
        data = dict(
            video_type=typ,
            name=params.name,
            src=src,
            story_id=story_id,
            contributor=user_id,
            upload_date=datetime.datetime.now()
        )
        vid = db.TblVideos.insert(**data)
        if params.video_date_datestr:
            rec = db(db.TblVideos.id==vid).select().first()
            date_data = dict(
                video_date_datestr=params.video_date_datestr,
                video_date_datespan=params.video_date_span
            )
            date_data_in = fix_record_dates_in(rec, date_data)
            rec.update_record(**date_data_in)
            data.update(video_date_datestr=params.video_date_datestr, video_date_datespan=params.video_date_datespan)
        else:
            data.update(video_date_datestr='1', video_date_datespan=0)
        ###update_record_dates(rec, date_info)
        ws_messaging.send_message(key='NEW-VIDEO', group='ALL', new_video_rec=data)
    else:
        old_rec = db(db.TblVideos.id==params.id).select().first()
        del params['src'] #
        #data = dict()
        #for fld in old_rec:
            #if fld in ('src', 'update_record', 'delete_record'):
                #continue
            #if old_rec[fld] != params[fld]:
                #data[fld] = params[fld]
        data = params
        if data:
            data_in = fix_record_dates_in(old_rec, data)
            old_rec.update_record(**data_in)
            update_record_dates(old_rec, date_info)
            if 'name' in data:
                sm = stories_manager.Stories()
                story_info = sm.get_story(old_rec.story_id)
                story_info.name = params.name
                sm.update_story(old_rec.story_id, story_info)
                ws_messaging.send_message(key='VIDEO-INFO-CHANGED', group='ALL', changes=data)
    return dict()

@serve_json
def delete_video(vars):
    story_id = db(db.TblVideos.id==vars.video_id).select().first().story_id
    sm = stories_manager.Stories()
    sm.delete_story(story_id)
    n = db(db.TblVideos.id==vars.video_id).update(deleted=True)
    return dict()

@serve_json
def get_video_list(vars):
    selected_topics = vars.selected_topics or []
    if selected_topics:
        lst = get_video_list_with_topics(vars)
    else:
        q = make_videos_query(vars)
        lst = db(q).select()
    selected_video_list = vars.selected_video_list
    result = []
    if selected_video_list:
        lst1 = db(db.TblVideos.id.belongs(selected_video_list)).select()
        lst1 = [rec for rec in lst1]
        for rec in lst1:
            rec.selected = True
    else:
        lst1 = []
    lst1_ids = [rec.id for rec in lst1]
    lst = [rec for rec in lst if rec.id not in lst1_ids]
    lst = lst1 + lst
    ##lst = db(db.TblVideos.deleted != True).select()
    video_list = [rec for rec in lst]
    for rec in video_list:
        fix_record_dates_out(rec)
    return dict(video_list=video_list)

def get_video_list_with_topics(vars):
    first = True
    topic_groups = calc_grouped_selected_options(vars.selected_topics)
    for topic_group in topic_groups:
        q = make_videos_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblVideos.id) & (db.TblItemTopics.item_type.like('%V%'))
        ##topic_ids = [t.id for t in topic_group]
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
        lst = db(q).select()
        lst = [rec.TblVideos for rec in lst]
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

def make_videos_query(vars):
    q = (db.TblVideos.deleted!=True)
    photographer_list = [p.option.id for p in vars.selected_photographers] if vars.selected_photographers else []
    if len(photographer_list) > 0:
        q &= db.TblVideos.photographer_id.belongs(photographer_list)
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblVideos.upload_date >= upload_date)
    opt = vars.selected_uploader
    if opt == 'mine':
        q &= (db.TblVideos.uploader==vars.user_id)
    elif opt == 'users':
        q &= (db.TblVideos.uploader!=None)
    opt = vars.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblVideos.video_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblVideos.video_date == NO_DATE)
    return q

def save_story_members(caller_id, caller_type, member_ids):
    if caller_type == "story":
        tbl = db.TblEvents
        tbl1 = db.TblEventMembers
        item_fld = tbl1.Event_id
    elif caller_type == "term":
        tbl = db.TblTerms
        tbl1 = db.TblTermMembers
        item_fld = db.TblTermMembers.term_id
    else:
        return dict()
    item = db(tbl.story_id==caller_id).select().first()
    qm = (item_fld==item.id) & (db.TblMembers.id==tbl1.Member_id)
    old_members = db(qm).select(db.TblMembers.id)
    old_members = [m.id for m in old_members]
    for m in old_members:
        if m not in member_ids:
            db((tbl1.Member_id==m) & (item_fld==item.id)).delete()
    for m in member_ids:
        if m not in old_members:
            if caller_type == "story":
                tbl1.insert(Member_id=m, Event_id=item.id)
            else:
                tbl1.insert(Member_id=m, term_id=item.id)
    return dict()

@serve_json
def apply_to_selected_videos(vars):
    all_tags = calc_all_tags()
    svl = vars.selected_video_list
    plist = vars.selected_photographers
    if len(plist) == 1:
        photographer_id = plist[0].option.id
    else:
        photographer_id = None
    if vars.photos_date_str:
        dates_info = dict(
            photo_date = (vars.photos_date_str, vars.photos_date_span_size)
        )
    else:
        dates_info = None

    st = vars.selected_topics
    added = []
    deleted = []
    changes = dict()
    for vid in svl:
        curr_tag_ids = set(get_tag_ids(vid, "V"))
        for tpc in st:
            topic = tpc.option
            item = dict(item_id=vid, topic_id=topic.id)
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                vrec = db(db.TblVideos.id==vid).select().first()
                story_id = vrec.story_id if vrec else None
                if not story_id:
                    continue
                new_id = db.TblItemTopics.insert(item_type="V", item_id=vid, topic_id=topic.id, story_id=story_id) 
                curr_tag_ids |= set([topic.id])
                added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if 'V' not in topic_rec.usage:
                    usage = topic_rec.usage + 'V'
                    topic_rec.update_record(usage=usage)
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=="V") & (db.TblItemTopics.item_id==vid) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[vid] = dict(keywords=keywords, video_id=vid)
        rec = db(db.TblVideos.id==vid).select().first()
        rec.update_record(keywords=keywords)
        if photographer_id:
            rec.update_record(photographer_id=photographer_id)
            rec1 = db(db.TblPhotographers.id==photographer_id).select().first()
            kind = rec1.kind or ''
            if not 'V' in kind:
                kind += 'V'
                rec1.update_record(kind=kind)
            changes[vid]['photographer_name'] = rec1.name
            changes[vid]['photographer_id'] = photographer_id
        if dates_info:
            update_record_dates(rec, dates_info)
    changes = [changes[vid] for vid in svl]
    ws_messaging.send_message('VIDEO-TAGS-CHANGED', group='ALL', changes=changes)
    return dict()

@serve_json
def add_story_member(vars):
    member_id = vars.candidate_id
    story_id = vars.story_id
    event = db(db.TblEvents.story_id==story_id).select().first()
    db.TblEventMembers.insert(Member_id=member_id, Event_id=event.id)
    return dict()

@serve_json
def save_photo_group(vars):
    story_id = vars.caller_id
    tbl = db.TblEvents if vars.caller_type == "story" else db.TblTerms if vars.caller_type == "term" else None
    if not tbl:
        raise Exception('Unknown call type in save photo group')
    item_id = db(tbl.story_id==story_id).select().first().id
    if vars.caller_type == "story":
        qp = (db.TblEventPhotos.Event_id==item_id) & (db.TblEventPhotos.Photo_id==db.TblPhotos.id) & (db.TblPhotos.deleted!=True)
    elif vars.caller_type == "term":
        qp = (db.TblTermPhotos.term_id==item_id) & (db.TblTermPhotos.Photo_id==db.TblPhotos.id) & (db.TblPhotos.deleted!=True)
    old_photos = db(qp).select(db.TblPhotos.id)
    old_photos = [p.id for p in old_photos]
    photo_ids = vars.photo_ids
    for p in old_photos:
        if p not in photo_ids:
            if vars.caller_type == "story":
                db((db.TblEventPhotos.Photo_id==p) & (db.TblEventPhotos.Event_id==item_id)).delete()
            elif  vars.caller_type == "term":
                db((db.TblTermPhotos.Photo_id==p) & (db.TblTermPhotos.term_id==item_id)).delete()
    for p in vars.photo_ids:
        if p not in old_photos:
            if vars.caller_type == "story":
                db.TblEventPhotos.insert(Photo_id=p, Event_id=item_id)
            elif vars.caller_type == "term":
                db.TblTermPhotos.insert(Photo_id=p, term_id=item_id)
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
    what = vars.what.upper()
    item_id = int(vars.item_id)
    rec = db((db.TblPageHits.what==what)&(db.TblPageHits.item_id==item_id)).select().first()
    if rec:
        rec.update_record(count=rec.count+1, new_count=(rec.new_count or 0) + 1)
    else:
        db.TblPageHits.insert(what=what, item_id=item_id, count=1, new_count=1)
    return dict()

@serve_json
def delete_selected_photos(vars):
    selected_photo_list = vars.selected_photo_list
    db(db.TblPhotos.id.belongs(selected_photo_list)).update(deleted=True)
    return dict()

@serve_json
def rotate_selected_photos(vars):
    selected_photo_list = vars.selected_photo_list
    for photo_id in selected_photo_list:
        rotate_photo(photo_id)
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
    qp = (db.TblEventPhotos.Event_id==event_id) & (db.TblPhotos.id==db.TblEventPhotos.Photo_id) & (db.TblPhotos.deleted!=True)
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
