import datetime
import random
import psutil

import stories_manager
import ws_messaging
from audios_support import audio_path
from dal_utils import insert_or_update
from date_utils import parse_date, update_record_dates, date_str, day_of_year, days_since_epoch
from docs_support import doc_url, doc_segment_url, doc_jpg_url, doc_segment_jpg_url
from gluon.utils import web2py_uuid
from html_utils import clean_html
from http_utils import json_to_storage
from members_support import *
from photos_support import get_slides_from_photo_list, get_video_thumbnails, save_member_face
from quiz_support import use_quiz
from words import calc_used_languages, read_words_index, get_all_story_previews, get_reisha
from family_connections import calc_family_connections, find_family_path, get_family_connections, get_member_spouse_children, get_spouses
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS

@serve_json
def member_list(vars):
    return dict(member_list=get_member_names())

@serve_json
def get_deceased_members(vars):
    return dict(members=_get_deceased_members())

@serve_json
def create_parent(vars):
    gender = vars.gender
    child_name = vars.child_name
    what = vars.parent_of + ' '
    name = what + child_name
    rec = new_member_rec(gender=gender, first_name=name)
    rec.member_info.updater_id = auth.current_user()
    rec.member_info.update_time = datetime.datetime.now()
    rec.member_info.approved = auth.has_membership(DATA_AUDITOR)
    rec.member_info.date_of_birth = NO_DATE
    rec.member_info.date_of_death = NO_DATE
    rec.member_info.story_id = new_bio(name)
    parent_id = db.TblMembers.insert(**rec.member_info)
    rec.member_info.id = parent_id
    rec.face_url = photos_folder(PROFILE_PHOTOS) + rec.facephotourl
    child_id = int(vars.child_id)
    if gender == 'M':
        db(db.TblMembers.id == child_id).update(father_id=parent_id)
    else:
        db(db.TblMembers.id == child_id).update(mother_id=parent_id)
    member_rec = get_member_rec(parent_id)
    ws_messaging.send_message(key='MEMBER_LISTS_CHANGED', group='ALL', member_rec=member_rec, new_member=True)
    return dict(member_id=parent_id, member=rec)


@serve_json
def create_new_member(vars):
    # todo: move code of photos/save_face to module and use it to complete the operation. in the client, go to
    #  the new member to edit its data
    # todo: refactor - use create_member to replace first part
    name = (vars.name or vars.default_name).strip() + ' '
    lst = name.split(' ')
    first_name, last_name = lst[0], ' '.join(lst[1:])
    first_name = first_name.strip()
    last_name = last_name.strip()
    name = name_from_first_last(first_name, last_name)
    rec = new_member_rec(first_name=first_name, last_name=last_name)
    rec.member_info.updater_id = auth.current_user()
    rec.member_info.update_time = datetime.datetime.now()
    rec.member_info.approved = auth.has_membership(DATA_AUDITOR)
    rec.member_info.date_of_birth = NO_DATE
    rec.member_info.date_of_death = NO_DATE
    rec.member_info.story_id = new_bio(name)
    member_id = db.TblMembers.insert(**rec.member_info)
    rec.member_info.id = member_id
    params = Storage(
        face=Storage(x=int(vars.face_x),
                     y=int(vars.face_y),
                     r=int(vars.face_r),
                     photo_id=int(vars.photo_id),
                     member_id=member_id),
        make_profile_photo=True
    )
    tmp = save_member_face(params)
    rec.member_info.face_photo_url = tmp.face_photo_url
    member_rec = get_member_rec(member_id)
    member_rec.facephotourl = tmp.face_photo_url
    member_rec = json_to_storage(member_rec)
    ws_messaging.send_message(key='MEMBER_LISTS_CHANGED', group='ALL', member_rec=member_rec, new_member=True)
    return dict(member_id=member_id, member=rec)

@serve_json
def create_spouse(vars):
    member_id, rec = create_member(vars)
    member_rec = get_member_rec(member_id)
    member_rec.facephotourl = photos_folder(PROFILE_PHOTOS) + "dummy_face.png"
    member_rec = json_to_storage(member_rec)
    ws_messaging.send_message(key='MEMBER_LISTS_CHANGED', group='ALL', member_rec=member_rec, new_member=True)
    return dict(member_id=member_id, member=rec)

def name_from_first_last(first_name, last_name):
    return ((first_name.strip() or "") + ' ' + (last_name.strip() or "")).strip()

def create_member(vars):
    name = (vars.name or vars.default_name).strip() + ' '
    lst = name.split(' ')
    first_name, last_name = lst[0], ' '.join(lst[1:])
    first_name = first_name.strip()
    last_name = last_name.strip()
    name = name_from_first_last(first_name, last_name)
    rec = new_member_rec(first_name=first_name, last_name=last_name)
    rec.member_info.updater_id = auth.current_user()
    rec.member_info.update_time = datetime.datetime.now()
    rec.member_info.approved = auth.has_membership(DATA_AUDITOR)
    rec.member_info.date_of_birth = NO_DATE
    rec.member_info.date_of_death = NO_DATE
    rec.member_info.gender = vars.gender
    rec.member_info.facephotourl="dummy_face.png"
    comment(f"before new bio({name})")
    rec.member_info.story_id = new_bio(name)
    comment(f"story id is {rec.member_info.story_id}")
    member_id = db.TblMembers.insert(**rec.member_info)
    rec.member_info.id = member_id
    rec.member_info.facephotourl = photos_folder(PROFILE_PHOTOS) + "dummy_face.png"
    return member_id, rec

@serve_json
def get_member_details(vars):
    if not vars.member_id:
        raise User_Error(T('Member does not exist yet!'))
    if vars.member_id == "new":
        rec = new_member_rec()
        rec.member_info.full_name = "members.new-member"
        return rec
    mem_id = int(vars.member_id)
    if vars.what == 'story':  # access member via its life story id
        rec = db(db.TblMembers.story_id == mem_id).select().first()
        if rec:
            mem_id = rec.id
        else:
            raise Exception('No member for this story {mid}', mem_id)
    if vars.shift == 'next':
        mem_id += 1
    elif vars.shift == 'prev':
        mem_id -= 1
    member_stories = get_member_stories(mem_id) + get_member_terms(mem_id) + \
        get_member_docs(mem_id) + \
        get_member_doc_segments(mem_id) + \
        get_member_video_stories(mem_id)
    member_info = get_member_rec(mem_id)
    if not member_info:
        raise User_Error('No one there')
    sm = stories_manager.Stories()
    story_info = sm.get_story(member_info.story_id) or Storage(display_version='New Story', topic="member.life-summary",
                                                               story_versions=[], story_text='', story_id=None, editing_ok=True)
    story_info.used_for = STORY4MEMBER
    family_connections = get_family_connections(member_info.id)
    slides = get_member_slides(mem_id)
    spouses = ''
    if family_connections.spouses:
        a_spouse = family_connections.spouses[0]
        spouse_gender = a_spouse.gender
        if spouse_gender == 'M':
            spouses = 'husband' + ('s' if len(family_connections.spouses) > 1 else '')
        else:
            spouses = 'wife' + ('s' if len(family_connections.spouses) > 1 else '')
    member_stories = [story_info] + member_stories
    return dict(member_info=member_info,
                story_info=story_info,
                family_connections=family_connections,
                slides=slides,  # todo: duplicate?
                spouses=spouses,  # this is just the key for translation
                member_stories=member_stories,
                facephotourl=photos_folder(PROFILE_PHOTOS) + (member_info.facephotourl or "dummy_face.png")
                )


@serve_json
def get_all_relatives(vars):
    member_id = vars.member_id
    relative_list=calc_family_connections(member_id)
    return dict(relative_list=relative_list)


@serve_json
def get_relatives_path(vars):
    origin_member_id = vars.origin_member_id
    other_member_id = vars.other_member_id
    relatives_path = find_family_path(origin_member_id, other_member_id)
    return dict(relatives_path=relatives_path)

@serve_json
def get_member_photo_list(vars):
    if vars.member_id == "new":
        return dict(photo_list=[])
    member_id = int(vars.member_id)
    if vars.what == 'story':
        rec = db(db.TblMembers.story_id == member_id).select().first()
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
    if vars.pinned:
        pin_story(story_info.story_id)
    return dict(info=info)


@serve_json
def approve_story_info(vars):
    user_id = vars.user_id
    story_info = vars.story_info
    story_id = int(story_info.story_id)
    rec = db(db.TblStories.id == story_id).select().first()
    db(db.TblStories.id == story_id).update(approved_version=rec.last_version)
    return dict()


@serve_json
def get_stories_index(vars):
    t0 = datetime.datetime.now()
    words_index = read_words_index()
    t1 = datetime.datetime.now()
    start = vars.start or 0
    start = int(start)
    length = len(words_index)
    chunk_size = 40000
    mem = psutil.virtual_memory();
    comment(f"getting stories idex. memory percent: {mem.percent}")
    words_index = words_index[start : start + chunk_size]
    return dict(stories_index=words_index, length=length )


@serve_json
def get_random_member(vars):
    if db(db.TblMembers.deleted != True).count() == 0:
        return dict(member_data = None)
    lst = []
    try:
        lst = get_members_stats()
    except Exception as e:
        lst = None
    if not lst:
        return dict(member_data=None)
    lst = sorted(lst, key=lambda rec: -rec.num_photos)
    member_data = None
    for i in range(50):
        idx = random.randint(0, len(lst) // 5)
        member_data = get_member_rec(lst[idx].member_id)
        if member_data:
            break
    if not member_data:
        return dict(member_data=None)
    member_data.face_photo_url = photos_folder(PROFILE_PHOTOS) + member_data.facephotourl
    member_data.short_name = (member_data.title + ' ' if member_data.title else '') + member_data.first_name
    return dict(member_data=member_data)


@serve_json
def get_stories_sample(vars):
    crec = db(db.TblConfiguration).select().first()
    expiration = crec.promoted_story_expiration
    if not expiration:
        expiration = 7
        crec.update_record(promoted_story_expiration=expiration)
    q = (db.TblStories.used_for == STORY4EVENT) & (db.TblStories.deleted == False) & (
                db.TblStories.visibility == SV_PUBLIC)
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=expiration)
    expiration_date = now - delta
    q1 = q & (db.TblStories.touch_time > expiration_date)
    lst1 = db(q1).select(limitby=(0, 10), orderby=~db.TblStories.touch_time)
    lst1 = [rec for rec in lst1]
    delta = datetime.timedelta(days=300)
    expiration_date = now - delta
    q2 = q & (db.TblStories.touch_time < expiration_date)
    lst2 = db(q2).select(limitby=(0, 200), orderby=~db.TblStories.story_len)
    lst2 = [rec for rec in lst2]
    n = 20 - len(lst1)
    if len(lst2) > n:
        lst2 = random.sample(lst2, n)
    lst = lst1 + lst2
    for r in lst:
        r.preview = get_reisha(r.preview, 16)
    return dict(stories_sample=lst)


@serve_json
def get_story_list(vars):
    params = vars.params
    qhd = query_has_data(vars.params)
    result1 = []
    result2 = []
    result3 = []
    result4 = []
    real_counters = None #will show true total numbers
    if params.selected_book:
        result0 = get_checked_stories(params)
        result0 = process_story_list(result0, checked=True)
        q = make_stories_query(params, True)
        q &= (db.TblStories.book_id == params.selected_book.id)
        result1 = db(q).select(orderby=db.TblStories.sorting_key)
        result1 = process_story_list(result1)
    elif qhd:
        result0 = get_checked_stories(params)
        result0 = process_story_list(result0, checked=True)
        checked_story_ids = set([r.id for r in result0])
        #-------------------------------------------------------------
        tmp = _get_story_list(params, exact=True)
        result1 = tmp[0] if tmp else []
        result1 = process_story_list(result1, exact=True)
        result1 = [r for r in result1 if r.id not in checked_story_ids]
        checked_story_ids |= set([r.id for r in result1])
        #-------------------------------------------------------------
        tmp = _get_story_list(params, exact=False)
        result2 = tmp[0] if tmp else []
        result2 = process_story_list(result2, exact=False)
        result2 = [r for r in result2 if r.id not in checked_story_ids]
        checked_story_ids |= set([r.id for r in result2])
        #-------------------------------------------------------------
        tmp = _get_story_list(params, exact=True, cuepoints=True)
        result3 = tmp[0] if tmp else []
        result3 = process_story_list(result3, exact=True)
        result3 = [r for r in result3 if r.id not in checked_story_ids]
        checked_story_ids |= set([r.id for r in result3])
        #-------------------------------------------------------------
        tmp = _get_story_list(params, exact=False, cuepoints=True)
        result4 = tmp[0] if tmp else []
        result4 = process_story_list(result4, exact=False)
        result4 = [r for r in result4 if r.id not in checked_story_ids]
    else:
        result0, real_counters = _get_story_list(params, False)
        result0 = process_story_list(result0)
    result = result0 + result1 + result2 + result3 + result4
    result_type_counters = dict()
    active_result_types = set()
    final_result = []
    for story in result:
        story_id = story.id
        k = story.used_for
        if k == STORY4DOCAB: #temp. debugging
            continue

        active_result_types |= {k}
        if k not in result_type_counters:
            result_type_counters[k] = 0
        result_type_counters[k] += 1
        story.doc_url = None
        story.doc_segment_url = None
        story.audio_path = None
        story.editable_preview = False
        if k == STORY4DOC:
            story.doc_url = doc_url(story_id)
        elif k == STORY4DOCSEGMENT:
            story.doc_segment_url = doc_segment_url(story_id)
        elif k == STORY4AUDIO:
            story.audio_path = audio_path(story_id)
        elif k == STORY4MEMBER:
            story.profile_photo_path = profile_photo_path(story_id)
        if result_type_counters[k] >= 100 and k != STORY4MEMBER:
            continue
        final_result.append(story)
    if real_counters:
        result_type_counters = real_counters #if no query data, return total, not sample size
    active_result_types = [k for k in active_result_types]
    active_result_types = sorted(active_result_types)
    result = final_result
    result = set_story_list_data(result)
    return dict(no_results=len(result)==0,
                result=result,
                active_result_types=active_result_types,
                result_type_counters=result_type_counters)

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
def get_app_description(vars):
    desc_name = '__description'
    sm = stories_manager.Stories()
    story = db(db.TblStories.name == desc_name).select().first()
    if story:
        story_id = story.id
    else:
        story_info = sm.get_empty_story(used_for=STORY4MESSAGE, story_text="Site description", name=desc_name)
        data = sm.add_story(story_info)
        story_id = data.story_id
    return dict(story=sm.get_story(story_id))


@serve_json
def get_story_detail(vars):
    story_id = vars.story_id
    sm = stories_manager.Stories()
    used_for = int(vars.used_for) if vars.used_for and vars.used_for != 'undefined' else STORY4EVENT
    if story_id == 'new':
        story = sm.get_empty_story(used_for=used_for)
        return dict(story=story, members=[], photos=[], story_date=dict(date="", span_size=None))
    story_id = int(story_id)
    story = sm.get_story(story_id)
    members = []
    candidates = []  # members found in the attached photos
    articles = []
    article_candidates = []
    photos = []
    if story.used_for == STORY4EVENT:
        event = db(db.TblEvents.story_id == story_id).select().first()
        if event:
            photos, members, candidates, articles, article_candidates = get_story_members(event)
    elif story.used_for == STORY4TERM:  # todo: try to consolidate with the above
        term = db(db.TblTerms.story_id == story_id).select().first()
        if term:
            photos, members, candidates, articles, article_candidates = get_term_members(term)
    story_topics = get_story_topics(story_id)
    story_rec = db(db.TblStories.id == story_id).select(db.TblStories.sorting_key, db.TblStories.story_date,
                                                        db.TblStories.book_id,
                                                        db.TblStories.story_date_dateunit,
                                                        db.TblStories.story_date_datespan).first()
    book_id = story_rec.book_id
    if book_id:
        book_name = db(db.TblBooks.id == book_id).select().first().name
        sorting_key = story_rec.sorting_key
        sorting_key = decode_sorting_key(sorting_key)
    else:
        book_name = None
        sorting_key = None
    dates = get_all_dates(story_rec)
    return dict(story=story, members=members, candidates=candidates,
                articles=articles, article_candidates=article_candidates,
                story_topics=story_topics, photos=photos, sorting_key=sorting_key, story_date=dates.story_date,
                book_id=book_id, book_name=book_name)


@serve_json
def get_story_photo_list(vars):
    story_id = vars.story_id
    if story_id == 'new':
        return dict(photo_list=[])
    story_id = int(story_id)
    if vars.story_type == "story":
        tbl = db.TblEvents
    elif vars.story_type == "term":
        tbl = db.TblTerms
    elif vars.story_type == "help":
        return dict(photo_list=[])
    else:
        raise Exception('Unknown call type in get story photo list')
    item = db(tbl.story_id == story_id).select().first()
    if item:
        item_id = item.id
    else:
        return dict(photo_list=[])
    if vars.story_type == "story":
        qp = (db.TblEventPhotos.event_id == item_id) & (db.TblPhotos.id == db.TblEventPhotos.photo_id)
    else:
        qp = (db.TblTermPhotos.term_id == item_id) & (db.TblPhotos.id == db.TblTermPhotos.photo_id)
    qp &= (db.TblPhotos.deleted != True)
    qp &= (db.TblStories.id == db.TblPhotos.story_id)
    photos = get_slides_from_photo_list(qp)
    return dict(photo_list=photos)


@serve_json
def save_member_info(vars):
    user_id = vars.user_id
    member_id = vars.member_id
    member_info = vars.member_info
    if 'facephotourl' in member_info:
        del member_info.facephotourl  # it is saved separately, not updated in client and can only destroy here
    if member_info:
        new_member = not member_info.id
        # --------------handle dates - new version------------------
        tbl = db.TblMembers
        for fld in tbl:
            if fld.type == 'date':
                fld_name = fld.name
                if fld_name + '_dateunit' not in member_info:
                    continue
                unit, date = parse_date(member_info[fld_name].date)
                member_info[fld_name] = date
                member_info[fld_name + '_dateunit'] = unit

        # --------------handle dates - end--------------------------
        member_info.update_time = datetime.datetime.now()
        member_info.updater_id = vars.user_id or auth.current_user() or 2
        member_info.approved = auth.has_membership(DATA_AUDITOR, user_id=vars.user_id)
        if member_info.spouse_id:
            marry(member_info.id, member_info.spouse_id, member_info.gender)
        result = insert_or_update(db.TblMembers, **member_info)
        if isinstance(result, dict):
            return dict(errors=result['errors'])
        member_id = result
        member_rec = get_member_rec(member_id)
        if new_member:
            member_rec.facephotourl = photos_folder(PROFILE_PHOTOS) + "dummy_face.png"
        member_rec = json_to_storage(member_rec)
        ws_messaging.send_message(key='MEMBER_LISTS_CHANGED', group='ALL', member_rec=member_rec, new_member=new_member)
    result = Storage(info=member_info)
    if member_id:
        result.member_id = member_id
    # todo: read-modify-write below?
    # get_member_names() #todo: needed if we use caching again
    return result


@serve_json
def set_member_story_id(vars):
    db(db.TblMembers.id == vars.member_id).update(story_id=vars.story_id)
    sm = stories_manager.Stories()
    sm.set_used_for(vars.story_id, STORY4MEMBER)
    return dict()


def get_member_names():
    q = (db.TblMembers.deleted != True)
    if db(q).isempty():
        return 
    lst = db(q).select()
    arr = [Storage(id=rec.id,
                   name=member_display_name(rec, full=True),
                   title='<span dir="rtl">' + member_display_name(rec, full=True) + '</span>',
                   first_name=rec.first_name,
                   last_name=rec.last_name,
                   former_first_name=rec.former_first_name,
                   former_last_name=rec.former_last_name,
                   nick_name=rec.nickname,
                   full_name=(rec.first_name or "") + ' ' + (rec.last_name or ""),
                   gender=rec.gender,
                   parent_ids=get_parent_ids(rec),
                   birth_date=rec.date_of_birth,
                   visibility=rec.visibility,
                   approved=rec.approved,
                   has_profile_photo=bool(rec.facephotourl),  # used in client!
                   rnd=random.randint(0, 1000000),
                   facephotourl=photos_folder(PROFILE_PHOTOS) + (rec.facephotourl or "dummy_face.png")) for rec in
           lst]
    arr.sort(key=lambda item: item.rnd)
    return arr

def _get_deceased_members():
    # have bio
    q = (db.TblMembers.deleted!=True)&(db.TblMembers.date_of_death!=NO_DATE)&(db.TblMembers.story_id==db.TblStories.id)
    lst = db(q).select(
        db.TblMembers.id,
        db.TblMembers.first_name,
        db.TblMembers.last_name,
        db.TblMembers.nickname,
        db.TblMembers.date_of_birth,
        db.TblMembers.date_of_birth_dateunit,
        db.TblMembers.date_of_death,
        db.TblMembers.date_of_death_dateunit,
        db.TblMembers.gender,
        db.TblMembers.facephotourl,
        db.TblStories.preview
        )
    arr = [Storage(
        id=rec.TblMembers.id,
        last_name=rec.TblMembers.last_name,
        full_name=(rec.TblMembers.first_name or "") + ' ' + (rec.TblMembers.last_name or ""),
        birth_date=date_str(rec.TblMembers.date_of_birth, rec.TblMembers.date_of_birth_dateunit),
        death_date=date_str(rec.TblMembers.date_of_death, rec.TblMembers.date_of_death_dateunit),
        death_day_of_year=day_of_year(rec.TblMembers.date_of_death),
        death_day_of_year_relative=day_of_year(rec.TblMembers.date_of_death, relative=True),
        death_day_since_epoch=days_since_epoch(rec.TblMembers.date_of_death),
        facephotourl=photos_folder(PROFILE_PHOTOS) + (rec.TblMembers.facephotourl or "dummy_face.png"),
        bio_preview=rec.TblStories.preview
    ) for rec in lst]
    # do not have bio
    q = (db.TblMembers.deleted!=True)&(db.TblMembers.date_of_death!=NO_DATE)&(db.TblMembers.story_id==None)
    lst = db(q).select(
        db.TblMembers.id,
        db.TblMembers.first_name,
        db.TblMembers.last_name,
        db.TblMembers.nickname,
        db.TblMembers.date_of_birth,
        db.TblMembers.date_of_birth_dateunit,
        db.TblMembers.date_of_death,
        db.TblMembers.date_of_death_dateunit,
        db.TblMembers.gender,
        db.TblMembers.facephotourl
        )
    arr1 = [Storage(
        id=rec.id,
        last_name=rec.last_name,
        full_name=(rec.first_name or "") + ' ' + (rec.last_name or ""),
        birth_date=date_str(rec.date_of_birth, rec.date_of_birth_dateunit),
        death_date=date_str(rec.date_of_death, rec.date_of_death_dateunit),
        death_day_of_year=day_of_year(rec.date_of_death),
        death_day_of_year_relative=day_of_year(rec.date_of_death, relative=True),
        death_day_since_epoch=days_since_epoch(rec.date_of_death),
        facephotourl=photos_folder(PROFILE_PHOTOS) + (rec.facephotourl or "dummy_face.png"),
        bio_preview=""
    ) for rec in lst]
    return arr + arr1

def get_parent_ids(member_rec):
    result = []
    for fld in ['father_id', 'mother_id', 'father2_id', 'mother2_id' ]:
        if member_rec[fld]:
            result.append(member_rec[fld])
    return result


@serve_json
def remove_member(vars):
    member_id = int(vars.member_id)
    mrec = db(db.TblMembers.id == member_id).select().first()
    # deleted = mrec.update_record(deleted=True) == 1
    mstory = db(db.TblStories.id==mrec.story_id).select().first()
    if mstory:
        mstory.update_record(deleted=True)
    mrec.update_record(deleted=True)
    ws_messaging.send_message(key='MEMBER_DELETED', group='ALL', member_id=member_id)
    return dict(deleted=True)


@serve_json
def remove_parent(vars):
    member_id = vars.member_id
    who = vars.who
    member_rec = db(db.TblMembers.id == member_id).select().first()
    if who == 'pa':
        member_rec.update_record(father_id=None)
    elif who == 'ma':
        member_rec.update_record(mother_id=None)
    elif who == 'pa2':
        member_rec.update_record(father2_id=None)
    elif who == 'ma2':
        member_rec.update_record(mother2_id=None)
    return dict()

@serve_json
def get_message_list(vars):
    pinned = db(db.TblPinned).select()
    pinned = [rec.story_id for rec in pinned]
    q = (db.TblStories.used_for == STORY4MESSAGE) & (db.TblStories.author_id == db.auth_user.id) & (
                db.TblStories.deleted != True)
    result = []
    for p in [True, False]:
        if p:
            q1 = q & (db.TblStories.id.belongs(pinned))
        else:
            q1 = q & (~db.TblStories.id.belongs(pinned))
        lst = db(q1).select(orderby=~db.TblStories.creation_date, limitby=(0, vars.limit or 100))
        result += [dict(story_text=rec.TblStories.story,
                        preview=rec.TblStories.story,  # it is short anyway
                        name=rec.TblStories.name,
                        story_id=rec.TblStories.id,
                        timestamp=rec.TblStories.last_update_date,
                        pinned=p,
                        author=rec.auth_user.first_name + ' ' + rec.auth_user.last_name) for rec in lst]
    return dict(message_list=result)


@serve_json
def push_message_up(vars):
    sid = vars.story_id
    rec = db(db.TblStories.id == sid).select().first()
    now = datetime.datetime.now()
    if rec:
        rec.update_record(creation_date=now, last_update_date=now)
    return dict()


@serve_json
def pin_message(vars):
    sid = vars.story_id
    q = (db.TblPinned.story_id == sid)
    pinned = False
    if db(q).isempty():
        db.TblPinned.insert(story_id=sid)
        pinned = True
    else:
        db(q).delete()
    return dict(pinned=pinned)




@serve_json
def get_used_languages(vars):
    return calc_used_languages(vars)


@serve_json
def get_term_list(vars):
    lst = db((db.TblStories.used_for == STORY4TERM) & \
             (db.TblStories.deleted != True) & \
             ###(db.TblTerms.deleted != True) & \
             (db.TblTerms.story_id == db.TblStories.id)).select(orderby=db.TblStories.name)
    result = [dict(story_text=rec.TblStories.story,
                   preview=get_reisha(rec.TblStories.preview, 40),
                   name=rec.TblStories.name,
                   story_id=rec.TblStories.id,
                   source=rec.TblStories.source,
                   id=rec.TblTerms.id) for rec in lst]
    return dict(term_list=result)


@serve_json
def delete_term(vars):
    rec = db(db.TblTerms.id == int(vars.term_id)).select().first()
    rec.update(deleted=True)
    story_id = rec.story_id
    db(db.TblStories.id == story_id).update(deleted=True)
    return dict()


@serve_json
def delete_checked_stories(vars):
    params = vars.params
    checked_stories = params.checked_story_list
    deleted = not params.deleted_stories  # will undelete if the list is of deleted stories
    q = db.TblStories.id.belongs(checked_stories)
    n = db(q).update(deleted=deleted)
    tbls = {STORY4MEMBER: db.TblMembers, STORY4EVENT: db.TblEvents, STORY4PHOTO: db.TblPhotos, STORY4TERM: db.TblTerms,
            STORY4VIDEO: db.TblVideos, STORY4DOC: db.TblDocs, STORY4DOCSEGMENT: db.TblDocSegments, 
            STORY4ARTICLE: db.TblArticles}

    # if story is associated with member, photo, video or document, need to skip it or delete the item too
    for usage in [STORY4MEMBER, STORY4EVENT, STORY4PHOTO, STORY4TERM, STORY4VIDEO, STORY4DOC, STORY4DOCSEGMENT,
                  STORY4AUDIO, STORY4ARTICLE]:
        q1 = q & (db.TblStories.used_for == usage)
        lst = db(q1).select()
        story_ids = [rec.id for rec in lst]
        if not story_ids:
            continue
        tbl = tbls[usage]
        db(tbl.story_id.belongs(story_ids)).update(deleted=deleted)
    return dict(num_deleted=n)


@serve_json
def burry_stories(vars):
    params = vars.params
    checked_stories = params.checked_story_list
    q = db.TblStories.id.belongs(checked_stories)
    n = db(q).update(dead=True)
    return dict(num_deleted=n)


@serve_json
def delete_story(vars):
    story_id = vars.story_id
    n = db(db.TblStories.id == story_id).update(deleted=True)
    return dict(deleted=n == 1)


@serve_json
def apply_topics_to_selected_stories(vars):
    used_for = vars.used_for
    if used_for:
        usage_chars = 'xMEPTxxxVDAxxxS'
        usage_char = usage_chars[used_for]
    else:
        usage_char = 'x'
    all_tags = calc_all_tags()
    params = vars.params
    stories_date_str = params.stories_date_str
    if stories_date_str:
        dates_info = dict(
            story_date=(stories_date_str, params.stories_date_span_size)
        )
    else:
        dates_info = None
    visibility_option = params.selected_story_visibility
    selected_book = params.selected_book

    checked_story_list = params.checked_story_list
    selected_topics = params.selected_topics
    new_topic_was_added = False
    # if selected_book and checked_story_list:  # we remove all stories and then add the ones from the selected books
    #    db(db.TblStories.book_id == selected_book.id).update(book_id=None)
    for story_id in checked_story_list:
        curr_tag_ids = set(get_tag_ids(story_id, usage_char))
        item_rec = item_of_story_id(used_for, story_id)
        for item in selected_topics:
            topic = item.option
            if topic.sign == "plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type=usage_char, story_id=story_id, topic_id=topic.id)
                curr_tag_ids |= {topic.id}
                ###added.append(item)
                topic_rec = db(db.TblTopics.id == topic.id).select().first()
                if topic_rec.topic_kind == 0:  # never used
                    new_topic_was_added = True
                if usage_char not in topic_rec.usage:
                    usage = topic_rec.usage + usage_char
                    topic_rec.update_record(usage=usage, topic_kind=2)  # topic is simple
            elif topic.sign == "minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type == usage_char) & (db.TblItemTopics.story_id == story_id) & (
                            db.TblItemTopics.topic_id == topic.id)
                curr_tag_ids -= {topic.id}
                ###deleted.append(item)
                # should remove usage_char from usage if it was the last one...
                db(q).delete()
        if dates_info:
            story_rec = db(db.TblStories.id == story_id).select().first()
            update_record_dates(story_rec, dates_info)
            copy_story_date_to_object_date(story_rec)
        if visibility_option:
            story_rec = db(db.TblStories.id == story_id).select().first()
            story_rec.update_record(visibility=visibility_option)
        if selected_book:
            story_rec = db(db.TblStories.id == story_id).select().first()
            story_rec.update_record(book_id=selected_book.id)

        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        curr_tags.sort()
        keywords = KW_SEP.join(curr_tags)
        rec = db(db.TblStories.id == story_id).select().first()
        rec.update_record(keywords=keywords, is_tagged=bool(keywords))

    # todo: notify all users?
    return dict(new_topic_was_added=new_topic_was_added)


@serve_json
def apply_topics_to_story(vars):
    story_id = vars.story_id
    used_for = vars.used_for
    if used_for:
        usage_chars = 'xMEPTxxxVDA'
        usage_char = usage_chars[used_for]
    else:
        usage_char = 'x'
    all_tags = calc_all_tags()
    story_topics = vars.story_topics
    current_ids = [topic.id for topic in story_topics]
    current_ids = set(current_ids)
    new_topic_was_added = False
    curr_tag_ids = set(get_tag_ids(story_id, usage_char))
    for topic_id in current_ids:
        if topic_id not in curr_tag_ids:
            new_id = db.TblItemTopics.insert(item_type=usage_char, story_id=story_id, topic_id=topic_id)
            curr_tag_ids |= {topic_id}
            ###added.append(item)
            topic_rec = db(db.TblTopics.id == topic_id).select().first()
            if topic_rec.topic_kind == 0:  # never used
                new_topic_was_added = True
            if usage_char not in topic_rec.usage:
                usage = topic_rec.usage + usage_char
                topic_rec.update_record(usage=usage, topic_kind=2)  # topic is simple
    for topic_id in curr_tag_ids:
        if topic_id not in current_ids:
            q = (db.TblItemTopics.item_type == usage_char) & (db.TblItemTopics.story_id == story_id) & (
                        db.TblItemTopics.topic_id == topic_id)
            ###deleted.append(item)
            # should remove usage_char from usage if it was the last one...
            db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = KW_SEP.join(curr_tags)
        rec = db(db.TblStories.id == story_id).select().first()
        rec.update_record(keywords=keywords, is_tagged=bool(keywords))

    # todo: notify all users?
    return dict(new_topic_was_added=new_topic_was_added)


@serve_json
def promote_stories(vars):
    checked_story_list = vars.params.checked_story_list
    q = (db.TblStories.id.belongs(checked_story_list))
    today = datetime.date.today()
    db(q).update(touch_time=today)
    return dict()


@serve_json
def save_group_members(vars):
    return save_story_members(vars.caller_id, vars.caller_type, vars.member_ids)


@serve_json
def add_story_member(vars):
    member_id = vars.candidate_id
    story_id = vars.story_id
    story = db(db.TblStories.id == story_id).select().first()
    if story.used_for == STORY4EVENT:
        event = db(db.TblEvents.story_id == story_id).select().first()
        db.TblEventMembers.insert(member_id=member_id, event_id=event.id)
    elif story.used_for == STORY4TERM:
        term = db(db.TblTerms.story_id == story_id).select().first()
        db.TblTermMembers.insert(member_id=member_id, term_id=term.id)
    else:
        raise Exception("Incompatible story usage")
    return dict()


@serve_json
def add_story_article(vars):
    article_id = vars.candidate_id
    story_id = vars.story_id
    story = db(db.TblStories.id == story_id).select().first()
    if story.used_for == STORY4EVENT:
        event = db(db.TblEvents.story_id == story_id).select().first()
        db.TblEventArticles.insert(article_id=article_id, event_id=event.id)
    elif story.used_for == STORY4TERM:
        term = db(db.TblTerms.story_id == story_id).select().first()
        db.TblTermArticles.insert(article_id=article_id, term_id=term.id)
    else:
        raise Exception("Incompatible story usage")
    return dict()


@serve_json
def save_photo_group(vars):
    story_id = vars.caller_id
    tbl = db.TblEvents if vars.caller_type == "story" else db.TblTerms if vars.caller_type == "term" else help if vars.caller_type == 'help' else None
    if not tbl:
        raise Exception('Unknown call type in save photo group')
    item_id = db(tbl.story_id == story_id).select().first().id
    if vars.caller_type == "story":
        qp = (db.TblEventPhotos.event_id == item_id) & (db.TblEventPhotos.photo_id == db.TblPhotos.id)
    elif vars.caller_type == "term":
        qp = (db.TblTermPhotos.term_id == item_id) & (db.TblTermPhotos.photo_id == db.TblPhotos.id)
    else:
        raise Exception("Unknown caller type")
    qp &= (db.TblPhotos.deleted != True)
    old_photos = db(qp).select(db.TblPhotos.id)
    old_photos = [p.id for p in old_photos]
    photo_ids = vars.photo_ids
    for p in old_photos:
        if p not in photo_ids:
            if vars.caller_type == "story":
                db((db.TblEventPhotos.photo_id == p) & (db.TblEventPhotos.event_id == item_id)).delete()
            elif vars.caller_type == "term":
                db((db.TblTermPhotos.photo_id == p) & (db.TblTermPhotos.term_id == item_id)).delete()
    for p in vars.photo_ids:
        if p not in old_photos:
            if vars.caller_type == "story":
                db.TblEventPhotos.insert(photo_id=p, event_id=item_id)
            elif vars.caller_type == "term":
                db.TblTermPhotos.insert(photo_id=p, term_id=item_id)
    photos = db(db.TblPhotos.id.belongs(photo_ids)).select(db.TblPhotos.id, db.TblPhotos.photo_path)
    photos = [p.as_dict() for p in photos]
    for p in photos:
        p['photo_path'] = photos_folder(RESIZED) + p['photo_path']
    return dict(photos=photos)


@serve_json
def consolidate_stories(vars):
    lst = vars.stories_to_merge
    lst = [(get_story_name(story_id), story_id) for story_id in lst]
    lst = sorted(lst)
    stm = [item[1] for item in lst]
    base_event_id = event_id_of_story_id(stm[0])
    # --------merge photos-------------------------
    base_photo_ids = set(get_story_photo_ids(stm[0]))
    added_photo_ids = set([])
    for story_id in stm[1:]:
        added_photo_ids |= set(get_story_photo_ids(story_id))
    added_photo_ids = added_photo_ids - base_photo_ids
    for pid in added_photo_ids:
        db.TblEventPhotos.insert(photo_id=pid, event_id=base_event_id)
    for pid in added_photo_ids:
        event_id = event_id_of_story_id(pid)
        db((db.TblEventPhotos.event_id == event_id) & (db.TblEventPhotos.photo_id == pid)).delete()
    # --------merge members--------------------------
    base_member_ids = set(get_story_member_ids(stm[0]))
    added_member_ids = set([])
    for story_id in stm[1:]:
        added_member_ids |= set(get_story_member_ids(story_id))
    added_member_ids = added_member_ids - base_member_ids
    for pid in added_member_ids:
        db.TblEventMembers.insert(member_id=pid, event_id=base_event_id)
    for pid in added_member_ids:
        event_id = event_id_of_story_id(pid)
        db((db.TblEventMembers.event_id == event_id) & (db.TblEventMembers.member_id == pid)).delete()
    # --------merge stories--------------------------
    story = get_story_text(stm[0])
    for i, story_id in enumerate(stm[1:]):
        name = lst[i + 1][0]
        story += '<br>----------' + name + '-------------------<br>'
        story += get_story_text(story_id)
    db(db.TblStories.id == stm[0]).update(story=story)
    # --------delete obsolete stories----------------
    db(db.TblStories.id.belongs(stm[1:])).update(deleted=True)
    return dict()


@serve_json
def clean_html_format(vars):
    html = clean_html(vars.html)
    return dict(html=html)


@serve_json
def count_hit(vars):
    what = vars.what.upper()
    item_id = int(vars.item_id)
    story_id, item_id = calc_hit_story_id(what, item_id)
    rec = db((db.TblPageHits.what == what) & (db.TblPageHits.item_id == item_id)).select().first()
    if rec:
        rec.update_record(count=rec.count + 1, new_count=(rec.new_count or 0) + 1)
    else:
        db.TblPageHits.insert(what=what, item_id=item_id, story_id=story_id, count=1, new_count=1)
    return dict()


@serve_json
def member_by_name(vars):
    name = vars.name + ' .'
    first_name, last_name = name.split()[:2]
    q = (db.TblMembers.deleted != True) & (db.TblMembers.first_name == first_name) & (
                db.TblMembers.last_name == last_name)
    members = db(q).select(db.TblMembers.id)
    member_ids = [rec.id for rec in members]
    return dict(member_ids=member_ids)


@serve_json
def save_sorting_key(vars):
    story_id = vars.story_id
    sorting_key = vars.sorting_key
    sorting_key = encode_sorting_key(sorting_key)
    db(db.TblStories.id == story_id).update(sorting_key=sorting_key)
    return dict()


@serve_json
def update_story_date(vars):
    story_date_str = vars.story_date_str
    story_date_datespan = int(vars.story_date_datespan or 0)
    if not story_date_str:
        story_date_str = '01-01-01'
    story_dates_info = dict(
        story_date=(story_date_str, story_date_datespan)
    )
    rec = db((db.TblStories.id == int(vars.story_id)) & (db.TblStories.deleted != True)).select().first()
    update_record_dates(rec, story_dates_info)
    # todo: save in db
    return dict()


@serve_json
def get_book_list(vars):
    lst = db(db.TblBooks).select()
    book_list = [rec.as_dict() for rec in lst]
    return dict(book_list=book_list)


@serve_json
def get_story_versions(vars):
    story_id = int(vars.story_id)
    sm = stories_manager.Stories()
    story_info = sm.get_story(story_id)
    last_update_date = story_info.last_update_date
    unapproved = story_info.approved_version < story_info.last_version
    prev_story_info = None
    updater = None
    author = auth.user_info(story_info.author_id)
    if unapproved and story_info.last_version > 0:
        try:
            prev_story_info = sm.get_story(story_id, to_story_version=story_info.approved_version)
        except Exception as e:
            log_exception("Failed to recover previous version")
            return dict(failed=True)
        txt = stories_manager.mark_diffs(prev_story_info.story_text, story_info.story_text)
        prev_story_info.story_text = txt
        updater = auth.user_info(story_info.updater_id)
    return dict(unapproved=unapproved, story_info=story_info, prev_story_info=prev_story_info, author=author,
                updater=updater, last_update_date=last_update_date)


###---------------------support functions

def new_member_rec(gender=None, first_name="", last_name=""):
    new_member = Storage(
        member_info=Storage(
            first_name=first_name,
            last_name=last_name,
            former_first_name="",
            former_last_name="",
            visibility=VIS_VISIBLE,
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
        story_info=Storage(display_version='New Story', story_versions=[], story_text='', story_id=None),
        family_connections=Storage(
            parents=dict(pa=None, ma=None),
            siblings=[],
            spouses=[],
            children=[]
        ),
        slides=[],
        spouses=[],
        member_stories=[],
        facephotourl='dummy_face.png',
        name=first_name
    )
    return new_member


def get_members_stats():
    q = (db.TblMembers.id == db.TblMemberPhotos.member_id) & \
        (db.TblMembers.deleted != True) & \
        (db.TblMembers.facephotourl != None) & (db.TblMembers.facephotourl != '')
    ##(db.TblMembers.id == db.TblEventMembers.member_id)
    lst = db(q).select(db.TblMembers.id, db.TblMembers.id.count(), groupby=[db.TblMembers.id])
    key = 'COUNT("TblMembers"."id")'
    lst = [Storage(member_id=rec.TblMembers.id, num_photos=rec._extra[key]) for rec in lst]
    return lst


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
                rec.source = ''
    else:
        checked_story_list = []
    return checked_story_list


def _get_story_list(params, exact, cuepoints=False):  # exact means looking only for the passed keywords string as a whole
    order_option = params.order_option.value if params.order_option else 'normal'
    q = make_stories_query(params, exact, cuepoints=cuepoints)
    real_counters = dict()
    if order_option == 'by-chats':
        q &= (db.TblStories.chatroom_id != None)
        lst1 = db(q).select(orderby=~db.TblStories.last_chat_time)
        lst1 = [r for r in lst1 if r.last_chat_time]
    elif order_option == 'by-update':
        q &= (db.TblStories.last_update_date != None)
        lst1 = db(q).select(orderby=~db.TblStories.last_update_date)
        lst1 = [r for r in lst1 if r.last_update_date]
    elif order_option == 'new-to-old':
        q &= (db.TblStories.story_date != NO_DATE)
        lst1 = db(q).select(orderby=~db.TblStories.story_date | db.TblStories.sorting_key | db.TblStories.name,
                            limitby=(0, 12000))
        lst1 = [r for r in lst1]
    elif order_option == 'old-to-new':
        q &= (db.TblStories.story_date != NO_DATE)
        lst1 = db(q).select(orderby=db.TblStories.story_date | db.TblStories.sorting_key | db.TblStories.name,
                            limitby=(0, 12000))
        lst1 = [r for r in lst1]
    elif order_option == 'by-name':
        lst1 = db(q).select(orderby=db.TblStories.sorting_key | db.TblStories.name, limitby=(0, 120000))
        lst1 = [r for r in lst1]
    elif not query_has_data(params):
        lst1 = []
        for used_for in story_kinds(params):
            q = (db.TblStories.deleted != True) & (db.TblStories.used_for == used_for)
            n = db(q).count()
            real_counters[used_for] = n
            if not n:
                continue
            sample_size = 100 if used_for != STORY4MEMBER else 500
            dic = None
            if n > sample_size:
                q1, dic = stories_random_sample(sample_size, used_for)
                q = q & q1
            lst0 = db(q).select()
            if dic:
                lst0 = [Storage(rec) for rec in lst0]
                for rec in lst0:
                    rec.idx = dic[rec.id]
                lst0.sort(key=lambda rec: rec.idx)
            lst1 += lst0
    else:
        if not q:
            return []
        lst1 = []
        for used_for in story_kinds(params):
            q1 = q & (db.TblStories.used_for == used_for)
            lst0 = db(q1).select(limitby=(0, 1000), orderby=~db.TblStories.story_len)
            lst1 += lst0
    return lst1, real_counters

def stories_random_sample(size, used_for):
    q = (db.TblStories.deleted != True) & (db.TblStories.used_for == used_for)
    lst = db(q).select(db.TblStories.id)
    lst = [rec.id for rec in lst]
    lst1 = random.sample(lst, size)
    dic = dict()
    for i, j in enumerate(lst1):
        dic[j] = i
    return db.TblStories.id.belongs(lst1), dic

def process_story_list(lst1, checked=False, exact=False):
    user_list = calc_user_list()
    lst = []
    for rec in lst1:
        if 'TblStories' in rec:
            r = rec.TblStories
        else:
            r = rec
        if r.author_id:
            user = user_list[r.author_id]
            r.author = user.first_name + ' ' + user.last_name
        else:
            r.author = ""
        r.checked = checked
        r.exact = exact
        lst.append(r)
    return lst


def set_story_list_data(story_list):
    user_list = auth.user_list()
    result = [Storage(
        story_text=rec.story,
        preview=rec.preview,
        name=rec.name,
        source=rec.source,
        story_id=rec.id,
        topics=rec.keywords,  ###'; '.join(story_topics[rec.id]) if rec.id in story_topics else "",
        doc_url=rec.doc_url,
        doc_segment_url=rec.doc_segment_url,
        audio_path=rec.audio_path,
        doc_jpg_url=calc_doc_jpg_url(rec.id, rec.used_for),
        profile_photo_path=rec.profile_photo_path if rec.used_for==STORY4MEMBER else "",
        used_for=rec.used_for,
        editable_preview=rec.editable_preview,
        event_date=rec.creation_date,
        timestamp=rec.last_update_date,
        updater=user_list[rec.updater_id] if rec.updater_id and rec.updater_id in user_list else dict(),
        checked=rec.checked,
        exact=rec.exact,
        sorting_key=rec.sorting_key,
        ##exact=exact and params.search_type != 'advanced',
        author=rec.source or rec.author) for rec in story_list]
    assign_photos(result)
    return result

def calc_doc_jpg_url(story_id, used_for):
    if used_for == STORY4DOC:
        return doc_jpg_url(story_id)
    if used_for == STORY4DOCSEGMENT:
        return doc_segment_jpg_url(story_id)
    return ""


def assign_photos(story_list):
    photo_story_list = dict()
    video_story_list = dict()
    for story in story_list:
        if story.used_for == STORY4PHOTO:
            photo_story_list[story.story_id] = story
        elif story.used_for == STORY4VIDEO:
            video_story_list[story.story_id] = story
    photo_story_ids = list(photo_story_list.keys())
    q = db.TblPhotos.story_id.belongs(photo_story_ids) & (db.TblPhotos.deleted != True)
    lst = db(q).select(db.TblPhotos.story_id, db.TblPhotos.photo_path, db.TblPhotos.id)
    for photo in lst:
        photo_src = photos_folder(SQUARES) + photo.photo_path
        photo_story_list[photo.story_id].photo_src = photo_src
        photo_story_list[photo.story_id].photo_id = photo.id
    video_story_ids = list(video_story_list.keys())
    lst = db(db.TblVideos.story_id.belongs(video_story_ids)).select(db.TblVideos.story_id, db.TblVideos.src, db.TblVideos.thumbnail_url)
    for video in lst:
        video_story_list[video.story_id].video_src = video.src
        video_story_list[video.story_id].thumbnail_url = video.thumbnail_url


def photo_member_ids(photo_id):
    qmp = (db.TblMemberPhotos.photo_id == photo_id)
    lst = db(qmp).select(db.TblMemberPhotos.member_id)
    return [mp.member_id for mp in lst]


def photo_article_ids(photo_id):
    qap = (db.TblArticlePhotos.photo_id == photo_id)
    lst = db(qap).select(db.TblArticlePhotos.article_id)
    return [ap.article_id for ap in lst]


def photo_lst_member_ids(photo_id_lst):
    result = set([])
    for photo_id in photo_id_lst:
        member_ids = photo_member_ids(photo_id)
        result |= set(member_ids)
    return result


def photo_lst_article_ids(photo_id_lst):
    result = set([])
    for photo_id in photo_id_lst:
        article_ids = photo_article_ids(photo_id)
        result |= set(article_ids)
    return result


def get_member_photos(member_id):
    q = (db.TblMemberPhotos.member_id == member_id) & \
        (db.TblPhotos.id == db.TblMemberPhotos.photo_id) & \
        (db.TblPhotos.deleted != True) & \
        (db.TblPhotos.is_back_side != True) & \
        (db.TblStories.id==db.TblPhotos.story_id)
    return get_slides_from_photo_list(q)

def get_member_videos(member_id):
    q = (db.TblMembersVideos.member_id==member_id) & \
        (db.TblVideos.id==db.TblMembersVideos.video_id) & \
        (db.TblVideos.deleted != True)
    return get_video_thumbnails(q)

def get_member_slides(member_id):
    lst1 = get_member_videos(member_id)
    lst2 = get_member_photos(member_id)
    #interlace videos and photos
    n = min(len(lst1), len(lst2))
    lst1_head, lst1_tail = lst1[:n],lst1[n:]
    lst2_head, lst2_tail = lst2[:n],lst2[n:]
    lst = []
    for i, x in enumerate(lst1_head):
        lst.append(x)
        lst.append(lst2[i])
    lst += lst1_tail + lst2_tail
    return lst

def save_story_data(story_info, user_id):
    story_info.sorting_key = encode_sorting_key(story_info.sorting_key)
    story_id = story_info.story_id
    sm = stories_manager.Stories(user_id)
    if isinstance(story_id, int):
        old_story = True
        result = sm.update_story(story_id, story_info)
    else:
        old_story = False
        result = sm.add_story(story_info)
    if story_info.used_for == STORY4PHOTO:
        photo_rec = db(
            (db.TblPhotos.story_id == story_info.story_id) & (db.TblPhotos.deleted != True)).select().first()
        photo_rec.update_record(name=story_info.name)
    if story_info.used_for == STORY4DOC:  # ugly... #todo: use only names in tblstories
        doc_rec = db(db.TblDocs.story_id==story_id).select().first()
        doc_rec.update_record(name=story_info.name)

    key = 'STORY_WAS_SAVED' if old_story else 'NEW_STORY_ADDED'
    ws_messaging.send_message(key=key, group='ALL', story_data=result)
    return result


def get_member_stories(member_id):
    q = (db.TblEventMembers.member_id == member_id) & \
        (db.TblEventMembers.event_id == db.TblEvents.id) & \
        (db.TblEvents.story_id == db.TblStories.id) & \
        (db.TblStories.deleted == False)
    result = []
    lst = db(q).select()
    for rec in lst:
        event = rec.TblEvents
        story = rec.TblStories
        dic = dict(
            topic=event.name,
            name=story.name,
            story_id=story.id,
            story_text=story.story,
            preview=get_reisha(story.preview, 30),
            source=event.ssource,
            used_for=story.used_for,
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date,
            language=story.language
        )
        result.append(dic)
    return result


def get_member_terms(member_id):
    q = (db.TblTermMembers.member_id == member_id) & \
        (db.TblTermMembers.term_id == db.TblTerms.id) & \
        (db.TblTerms.story_id == db.TblStories.id) & \
        (db.TblStories.deleted == False)
    result = []
    lst = db(q).select()
    for rec in lst:
        term = rec.TblTerms
        story = rec.TblStories
        dic = dict(
            topic=term.name,
            name=story.name,
            story_id=story.id,
            story_text=story.story,
            preview=get_reisha(story.preview, 30),
            ###source = term.ssource,
            used_for=story.used_for,
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date
        )
        result.append(dic)
    return result

def get_member_docs(member_id):
    q = (db.TblMembersDocs.member_id == member_id) & \
        (db.TblMembersDocs.doc_id == db.TblDocs.id) & \
        (db.TblDocs.story_id == db.TblStories.id) & \
        (db.TblStories.deleted == False)
    result = []
    lst = db(q).select()
    for rec in lst:
        doc = rec.TblDocs
        story = rec.TblStories
        dic = dict(
            topic=doc.name,
            name=story.name,
            story_id=story.id,
            story_text=story.story,
            preview=get_reisha(story.preview, 30),
            ###source = term.ssource,
            used_for=story.used_for,
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date
        )
        result.append(dic)
    return result

def get_member_doc_segments(member_id):
    q = (db.TblMembersDocSegments.member_id == member_id) & \
        (db.TblMembersDocSegments.doc_segment_id == db.TblDocSegments.id) & \
        (db.TblDocSegments.story_id == db.TblStories.id) & \
        (db.TblStories.deleted == False)
    result = []
    lst = db(q).select()
    for rec in lst:
        story = rec.TblStories
        dic = dict(
            topic=story.name,
            name=story.name,
            story_id=story.id,
            story_text=story.story,
            preview=get_reisha(story.preview, 30),
            ###source = term.ssource,
            used_for=story.used_for,
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date
        )
        result.append(dic)
    return result

def get_member_video_stories(member_id):
    q = (db.TblMembersVideos.member_id == member_id) & \
        (db.TblMembersVideos.video_id == db.TblVideos.id) & \
        (db.TblVideos.story_id == db.TblStories.id) & \
        (db.TblStories.deleted == False)
    result = []
    lst = db(q).select()
    for rec in lst:
        video = rec.TblVideos
        story = rec.TblStories
        if not story.story:
            continue
        dic = dict(
            topic=video.name,
            name=story.name,
            story_id=story.id,
            story_text=story.story,
            preview=get_reisha(story.preview, 30),
            ###source = term.ssource,
            used_for=story.used_for,
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date
        )
        result.append(dic)
    return result

def query_has_data(params):
    first_year, last_year = calc_years_range(params)
    return params.keywords_str or params.checked_story_list or params.selected_stories or \
           (params.days_since_update and params.days_since_update.value) or first_year or last_year or \
           (params.approval_state and params.approval_state.id in [2, 3]) or params.selected_topics or \
           params.show_untagged or params.selected_words or params.deleted_stories

def keywords_query(q, keywords_str, exact):
    if exact:
        single = len(keywords_str.split()) == 1
        if single:
            q1 = (db.TblStories.name.regexp(r"\y" + keywords_str + r"\y")) | (
                    db.TblStories.story.regexp(r"\y" + keywords_str + r"\y"))
        else:
            q1 = (db.TblStories.name.contains(keywords_str)) | \
                    (db.TblStories.story.contains(keywords_str))
        q &= q1
    else:
        keywords = keywords_str.split()
        for kw in keywords:
            q &= (db.TblStories.name.contains(kw)) | (db.TblStories.story.contains(kw))
    return q

def cuepoints_text_query(q, keywords_str, exact):
    q1 = (db.TblStories.used_for == STORY4VIDEO) & (db.TblVideos.story_id==db.TblStories.id)
    if exact:
        single = len(keywords_str.split()) == 1 
        if single:
            q1 &= (db.TblVideos.cuepoints_text.regexp(r"\y" + keywords_str + r"\y"))
        else:
            q1 &= (db.TblVideos.cuepoints_text.contains(keywords_str))
    else:
        keywords = keywords_str.split()
        for kw in keywords:
            q1 &= (db.TblVideos.cuepoints_text.contains(kw))
    q &= q1
    return q
        
def make_stories_query(params, exact, cuepoints=False):
    q = init_query(db.TblStories, editing=params.editing, is_deleted=params.deleted_stories)
    q &= (db.TblStories.used_for.belongs(story_kinds(params)))
    selected_stories = params.selected_stories
    keywords_str = params.keywords_str
    if keywords_str:
        selected_stories = []
        if cuepoints:
            q = cuepoints_text_query(q, keywords_str, exact)
        else:
            q = keywords_query(q, keywords_str, exact)
    if selected_stories:
        q &= (db.TblStories.id.belongs(selected_stories))
    if params.days_since_update and params.days_since_update.value:
        date0 = datetime.datetime.now() - datetime.timedelta(days=params.days_since_update.value)
        q &= (db.TblStories.last_update_date > date0)
    if params.approval_state:
        if params.approval_state.id == 2:
            q &= (db.TblStories.last_version > db.TblStories.approved_version)
        if params.approval_state.id == 3:
            q &= (db.TblStories.last_version == db.TblStories.approved_version)
    first_year, last_year = calc_years_range(params)
    if first_year:
        from_date = datetime.date(year=first_year, month=1, day=1)
        q &= (db.TblStories.story_date_dateend > from_date)
    if last_year:
        to_date = datetime.date(year=last_year, month=1, day=1)
        q &= (db.TblStories.story_date < to_date)
    if params.show_untagged:
        q &= (db.TblStories.is_tagged == False)
    if params.start_name:
        q &= (db.TblStories.name >= params.start_name)
    if params.selected_topics:
        q1 = get_topics_query(params.selected_topics)
        q &= q1
    return q


def calc_years_range(params):
    first_year = params.first_year
    last_year = params.last_year
    if params.base_year:  # time range may be defined
        if first_year < params.base_year + 4:
            first_year = 0
        if last_year and last_year > params.base_year + params.num_years - 5:
            last_year = 0
    return (first_year, last_year)


def _merge_members(mem1_id, mem2_id):
    photos1 = db(db.TblMemberPhotos.member_id == mem1_id).select()
    photos2 = db(db.TblMemberPhotos.member_id == mem2_id).select()
    set1 = set([rec.photo_id for rec in photos1])
    set2 = set([rec.photo_id for rec in photos2])
    for rec in photos2:
        if rec.photo_id in set1:
            db(db.TblMemberPhotos.id == rec.id).delete()
        else:
            rec.update_record(member_id=mem1_id)
    db(db.TblMembers.id == mem2_id).update(deleted=True)


def merge_members():
    mem1 = int(request.vars.mem1)
    mem2 = int(request.vars.mem2)
    _merge_members(mem1, mem2)
    return "Members merged"


def save_story_members(caller_id, caller_type, member_ids):
    if caller_type == "story":
        tbl = db.TblEvents
        tbl1 = db.TblEventMembers
        item_fld = tbl1.event_id
    elif caller_type == "term":
        tbl = db.TblTerms
        tbl1 = db.TblTermMembers
        item_fld = db.TblTermMembers.term_id
    else:
        return dict()
    item = db(tbl.story_id == caller_id).select().first()
    qm = (item_fld == item.id) & (db.TblMembers.id == tbl1.member_id)
    old_members = db(qm).select(db.TblMembers.id)
    old_members = [m.id for m in old_members]
    for m in old_members:
        if m not in member_ids:
            db((tbl1.member_id == m) & (item_fld == item.id)).delete()
    for m in member_ids:
        if m not in old_members:
            if caller_type == "story":
                tbl1.insert(member_id=m, event_id=item.id)
            else:
                tbl1.insert(member_id=m, term_id=item.id)
    return dict()


def get_story_text(story_id):
    rec = db(db.TblStories.id == story_id).select().first()
    if rec:
        return rec.story
    else:
        return ''


def get_story_name(story_id):
    rec = db(db.TblStories.id == story_id).select().first()
    if rec:
        return rec.name
    else:
        return ''


def event_id_of_story_id(story_id):
    rec = db(db.TblEvents.story_id == story_id).select().first()
    if rec:
        return rec.id
    else:
        return None


def get_story_photo_ids(story_id):
    event_id = event_id_of_story_id(story_id)
    if not event_id:
        return []
    qp = (db.TblEventPhotos.event_id == event_id) & (db.TblPhotos.id == db.TblEventPhotos.photo_id) & (
                db.TblPhotos.deleted != True)
    lst = db(qp).select(db.TblPhotos.id)
    lst = [p.id for p in lst]
    return lst


def get_story_member_ids(story_id):
    event_id = event_id_of_story_id(story_id)
    if not event_id:
        return []
    qm = (db.TblEventMembers.event_id == event_id) & (db.TblMembers.id == db.TblEventMembers.member_id)
    lst = db(qm).select(db.TblMembers.id)
    lst = [m.id for m in lst]
    return lst


def item_of_story_id(used_for, story_id):
    tbls = {
        STORY4MEMBER: db.TblMembers,
        STORY4EVENT: db.TblEvents,
        STORY4PHOTO: db.TblPhotos,
        STORY4TERM: db.TblTerms,
        STORY4MESSAGE: None,
        STORY4HELP: None,
        STORY4FEEDBACK: None,
        STORY4VIDEO: db.TblVideos,
        STORY4DOC: db.TblDocs,
        STORY4DOCSEGMENT: db.TblDocSegments,
        STORY4AUDIO: db.TblAudios,
        STORY4ARTICLE: db.TblArticles
    }
    tbl = tbls[used_for]
    if tbl:
        rec = db(tbl.story_id == story_id).select().first()
        if rec:
            return rec
    return None


def copy_story_date_to_object_date(story_rec):
    if story_rec.used_for == STORY4EVENT:
        event_rec = db(db.TblEvents.story_id == story_rec.id).select().first()
        event_rec.update_record(event_date=story_rec.story_date,
                                event_date_dateunit=story_rec.story_date_dateunit,
                                event_date_datespan=story_rec.story_date_datespan,
                                event_date_dateend=story_rec.story_date_dateend,
                                )
    elif story_rec.used_for == STORY4PHOTO:
        photo_rec = db(db.TblPhotos.story_id == story_rec.id).select().first()
        photo_rec.update_record(photo_date=story_rec.story_date,
                                photo_date_dateunit=story_rec.story_date_dateunit,
                                photo_date_datespan=story_rec.story_date_datespan,
                                photo_date_dateend=story_rec.story_date_dateend,
                                )
    elif story_rec.used_for == STORY4VIDEO:
        video_rec = db(db.TblVideos.story_id == story_rec.id).select().first()
        video_rec.update_record(video_date=story_rec.story_date,
                                video_date_dateunit=story_rec.story_date_dateunit,
                                video_date_datespan=story_rec.story_date_datespan,
                                video_date_dateend=story_rec.story_date_dateend,
                                )
    elif story_rec.used_for == STORY4DOC:
        doc_rec = db(db.TblDocs.story_id == story_rec.id).select().first()
        doc_rec.update_record(doc_date=story_rec.story_date,
                              doc_date_dateunit=story_rec.story_date_dateunit,
                              doc_date_datespan=story_rec.story_date_datespan,
                              doc_date_dateend=story_rec.story_date_dateend,
                              )
    elif story_rec.used_for == STORY4DOCSEGMENT:
        doc_seg_rec = db(db.TblDocsegments.story_id == story_rec.id).select().first()
        doc_seg_rec.update_record(doc_seg_date=doc_seg_rec.story_date,
                              doc_seg_date_dateunit=doc_seg_rec.story_date_dateunit,
                              doc_seg_date_datespan=doc_seg_rec.story_date_datespan,
                              doc_seg_date_dateend=doc_seg_rec.story_date_dateend,
                              )
    elif story_rec.used_for == STORY4AUDIO:
        audio_rec = db(db.TblAudios.story_id == story_rec.id).select().first()
        audio_rec.update_record(audio_date=story_rec.story_date,
                                audio_date_dateunit=story_rec.story_date_dateunit,
                                audio_date_datespan=story_rec.story_date_datespan,
                                audio_date_dateend=story_rec.story_date_dateend,
                                )
    # elif story_rec.used_for == STORY4ARTICLE:
    # article_rec = db(db.Tblarticles.story_id==story_rec.id).select().first()
    # article_rec.update_record(article_date=story_rec.story_date,
    # article_date_dateunit=story_rec.story_date_dateunit,
    # article_date_datespan=story_rec.story_date_datespan,
    # article_date_dateend=story_rec.story_date_dateend,
    # )


@serve_json
def qualified_members(vars):
    checked_answers = vars.checked_answers
    nota_questions = vars.nota_questions
    qualified_members = use_quiz(checked_answers, nota_questions)
    if nota_questions:
        lst = db(~db.TblMembers.id.belongs(qualified_members)).select(db.TblMembers.id)
        qualified_members = [mem.id for mem in lst]
    return dict(qualified_members=qualified_members)

@serve_json
def check_duplicates(vars):
    return dict(duplicates=check_dups())

@serve_json
def collect_search_stats(vars):
    rec = db(db.TblSearches.pattern == vars.search_pattern).select().first()
    if rec:
        rec.update_record(count=rec.count + 1)
    else:
        db.TblSearches.insert(pattern=vars.search_pattern, count=1)

@serve_json
def divorce(vars):
    member_id = int(vars.member_id)
    spouse_id = int(vars.spouse_id)
    if vars.what == "undo-divorce":
        value = 0
    else:
        value = int(vars.hide_spouse)
    children = get_member_spouse_children(member_id, spouse_id)
    for child in children:
        child.update_record(parents_marital_status=value)
    spouses = get_spouses(member_id)
    return dict(spouses=spouses)

def story_kinds(params):
    if (params.events_only):
        return [STORY4EVENT]
    story_kinds_arr = STORY4USER
    if auth.user_has_privilege(HELP_AUTHOR):
        story_kinds_arr += [STORY4HELP]
    if auth.user_has_privilege(ADMIN):
        story_kinds_arr += [STORY4MESSAGE]
    return story_kinds_arr


def get_story_members(event):
    qp = (db.TblEventPhotos.event_id == event.id) & (db.TblPhotos.id == db.TblEventPhotos.photo_id) & (
                db.TblPhotos.deleted != True)
    photos = db(qp).select(db.TblPhotos.id, db.TblPhotos.photo_path)
    photo_ids = [photo.id for photo in photos]
    photo_member_set = photo_lst_member_ids(photo_ids)
    photo_article_set = photo_lst_article_ids(photo_ids)

    photos = [p.as_dict() for p in photos]
    for p in photos:
        p['photo_path'] = photos_folder(RESIZED) + p['photo_path']
    member_fields = [db.TblMembers.id, db.TblMembers.first_name, db.TblMembers.last_name, db.TblMembers.facephotourl]
    # -----------------members-------------------
    qm = (db.TblEventMembers.event_id == event.id) & (db.TblMembers.id == db.TblEventMembers.member_id) & (
                db.TblMembers.deleted != True)
    qa = (db.TblEventArticles.event_id == event.id) & (db.TblArticles.id == db.TblEventArticles.article_id)
    return _info_from_qm(qm, qa, member_fields, photo_member_set, photo_article_set, photos)


def get_term_members(term):
    member_fields = [db.TblMembers.id, db.TblMembers.first_name, db.TblMembers.last_name, db.TblMembers.facephotourl]
    qp = (db.TblTermPhotos.term_id == term.id) & (db.TblPhotos.id == db.TblTermPhotos.photo_id) & (
                db.TblPhotos.deleted != True)
    photos = db(qp).select(db.TblPhotos.id, db.TblPhotos.photo_path)
    photo_ids = [photo.id for photo in photos]
    photo_member_set = photo_lst_member_ids(photo_ids)
    photo_article_set = photo_lst_article_ids(photo_ids)

    photos = [p.as_dict() for p in photos]
    for p in photos:
        p['photo_path'] = photos_folder(RESIZED) + p['photo_path']
    # -----------------members-------------------
    qm = (db.TblTermMembers.term_id == term.id) & (db.TblMembers.id == db.TblTermMembers.member_id)
    qa = (db.TblTermArticles.term_id == term.id) & (db.TblArticles.id == db.TblTermArticles.article_id)
    return _info_from_qm(qm, qa, member_fields, photo_member_set, photo_article_set, photos)


def _info_from_qm(qm, qa, member_fields, photo_member_set, photo_article_set, photos):
    members = db(qm).select(*member_fields)
    members = [m for m in members]
    member_set = set([m.id for m in members])
    added_members_from_photos = photo_member_set - member_set
    added_members_lst = [mid for mid in added_members_from_photos]
    added_members = db(db.TblMembers.id.belongs(added_members_lst)).select(*member_fields)
    candidates = [m.as_dict() for m in added_members]
    members = [m.as_dict() for m in members]
    # ------------------articles-----------------------
    articles = db(qa).select()
    articles = [a.TblArticles for a in articles]
    article_set = set([a.id for a in articles])
    added_articles_from_photos = photo_article_set - article_set
    added_articles_lst = [aid for aid in added_articles_from_photos]
    added_articles = db(db.TblArticles.id.belongs(added_articles_lst)).select()
    article_candidates = [a.as_dict() for a in added_articles]
    articles = [a.as_dict() for a in articles]
    # --------------------------------------------------
    lst = [members, candidates]
    for arr in lst:
        for m in arr:
            m['full_name'] = (m['first_name'] or '') + ' ' + (m['last_name'] or '')
            if not m['facephotourl']:
                m['facephotourl'] = "dummy_face.png"
            m['facephotourl'] = photos_folder(PROFILE_PHOTOS) + m['facephotourl']
    lst = [articles, article_candidates]
    for arr in lst:
        for a in arr:
            a['facephotourl'] = photos_folder(PROFILE_PHOTOS) + a['facephotourl']
    return photos, members, candidates, articles, article_candidates


def encode_sorting_key(sk):
    if not sk:
        return ""
    sk = ['{:03}'.format(int(k)) for k in sk if k]
    return '-'.join(sk)


def decode_sorting_key(sk):
    sk = sk.strip()
    if not sk:
        return []
    lst = sk.split('-')
    return [int(s) for s in lst]

def marry(member_id, spouse_id, member_gender):
    spouse_rec = get_member_rec(spouse_id)
    spouse_gender = spouse_rec.gender
    info = Storage()
    if member_gender == "M":
        info.father_id = member_id;
        if spouse_gender != member_gender:
            info.mother_id = spouse_id
        else:
            info.father2_id = spouse_id
    if member_gender == "F":
        info.mother_id = member_id;
        if spouse_gender != member_gender:
            info.father_id = spouse_id
        else:
            info.mother2_id = spouse_id
    info.visibility = 0
    info.story_id = new_bio("???") 
    child_id = db.TblMembers.insert(**info)
