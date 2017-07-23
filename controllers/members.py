import stories_manager
from gluon.storage import Storage
from gluon.utils import web2py_uuid
from my_cache import Cache
import ws_messaging
from http_utils import json_to_storage
import datetime
import os
from dal_utils import insert_or_update
from photos import get_slides_from_photo_list, photos_folder, local_photos_folder, crop, save_uploaded_photo
import random
import zlib
import re

MAX_PHOTOS_COUNT = 1200

@serve_json
def member_list(vars):
    return dict(member_list=get_member_names(vars.visible_only, vars.gender))

@serve_json
def create_parent(vars):
    gender = vars.gender
    child_name = vars.child_name
    what = 'Pa ' if gender == 'M' else 'Ma '
    rec = new_member_rec(gender=gender, first_name=what + child_name)
    parent_id = db.TblMembers.insert(**rec.member_info)
    rec.member_info.id = parent_id
    return dict(member_id=parent_id, member=rec)

def new_member_rec(gender=None, first_name=""):
    new_member = Storage(
        member_info=Storage(
            first_name=first_name,
            last_name="",
            former_first_name="",
            former_last_name="",
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
        facePhotoURL = request.application + '/static/images/dummy_face.png',
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
    family_connections = get_family_connections(member_info)
    slides = get_member_slides(mem_id)
    if member_info.gender == 'F':
        spouses = 'husband' + ('s' if len(family_connections.spouses) > 1 else '')
    else:
        spouses = 'wife' + ('s' if len(family_connections.spouses) > 1 else '')
    member_stories = [story_info] + member_stories;
    return dict(member_info=member_info, story_info=story_info, family_connections=family_connections, 
                slides=slides, #todo: duplicate?
                spouses=spouses, #this is just the key for translation
                member_stories=member_stories,
                facePhotoURL = photos_folder('profile_photos') + member_info.facePhotoURL if  member_info.facePhotoURL else request.application + '/static/images/dummy_face.png')

@serve_json
def get_member_photo_list(vars):
    member_id = int(vars.member_id)
    slides = get_member_slides(member_id)
    return dict(photo_list=slides)

@serve_json
def save_story_info(vars):
    user_id = vars.user_id
    story_info = vars.story_info
    story_id = save_story_data(story_info, used_for=STORY4MEMBER, user_id=user_id)
    return dict(story_id=story_id)

@serve_json
def get_random_member(vars):
    lst = get_members_stats()
    lst = sorted(lst, key=lambda rec: -rec.num_photos)
    idx = random.randint(0, len(lst) / 5)
    member_data=get_member_rec(lst[idx].member_id)
    result = dict(face_photo_url=photos_folder('profile_photos') + member_data.facePhotoURL,
                  name=member_data.full_name,
                  year_of_birth=member_data.date_of_birth.year if member_data.date_of_birth else None,           
                  year_of_death=member_data.date_of_death.year if member_data.date_of_death else None,
                  place_of_birth=member_data.PlaceOfBirth,
                  gender=member_data.gender,
                  id=member_data.id
                  )
    return dict(member_data=result)

def get_members_stats():
    q = (db.TblMembers.id == db.TblMemberPhotos.Member_id) & \
        (db.TblMembers.facePhotoURL != None) & (db.TblMembers.facePhotoURL != '')
        ##(db.TblMembers.id == db.TblEventMembers.Member_id)
    lst = db(q).select(db.TblMembers.id, db.TblMembers.id.count(), groupby=[db.TblMembers.id])
    lst = [Storage(member_id=rec.TblMembers.id, num_photos=rec._extra['COUNT(TblMembers.id)']) for rec in lst]
    return lst

@serve_json
def get_stories_sample(vars):
    q = db.TblStories.used_for==STORY4EVENT
    lst = db(q).select(limitby=(0, 100), orderby=~db.TblStories.story_length)
    lst1 = random.sample(lst, 10)
    return dict(stories_sample=lst1)

@serve_json
def save_member_info(vars):
    user_id = vars.user_id
    story_info = vars.story_info
    if story_info:
        story_id = save_story_data(story_info, used_for=STORY4MEMBER, user_id=user_id)
    else:
        story_id = None
    member_id = vars.member_id
    member_info = vars.member_info
    if member_info:
        new_member = not member_info.id
        if story_id:
            member_info.story_id = story_id
        date_fields = []
        for k in member_info:
            if k.startswith("date_of_") and k.endswith('_str'):
                date_fields.append(k)
        for df in date_fields:
            k = df[:-4]
            member_info[k] = date_of_partial_date(member_info[df])
        result = insert_or_update(db.TblMembers, **member_info)
        if isinstance(result, dict):
            return dict(errors=result['errors'])
        member_id = result
        member_rec = get_member_rec(member_id)
        member_rec = json_to_storage(member_rec)
        ws_messaging.send_message(key='MEMBER_LISTS_CHANGED', group='ALL_USERS', member_rec=member_rec, new_member=new_member)
    elif story_id:
        db(db.TblMembers.id==member_id).update(story_id=story_id)
    result = Storage(story_id=story_id)
    if member_id:
        result.member_id = member_id;
    return result

@serve_json
def upload_photos(vars):
    user_id = vars.user_id or auth.current_user()
    comment("start handling uploaded files")
    today = datetime.date.today()
    month = str(today)[:-3]

    path = local_photos_folder() + 'uploads/' + month + '/'
    number_uploaded = 0
    number_duplicates = 0
    failed = []
    if not os.path.isdir(path):
        os.makedirs(path)
    user_id = int(vars.user_id) if vars.user_id else None
    for fn in vars:
        if fn.startswith('user'):
            continue
        fil = vars[fn]
        crc = zlib.crc32(fil.BINvalue)
        cnt = db(db.TblPhotos.crc==crc).count()
        if cnt > 0:
            number_duplicates += 1
            continue

        original_file_name, ext = os.path.splitext(fil.name)
        file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
        result = save_uploaded_photo(file_name, fil.BINvalue, 'uploads/' + month + '/', original_file_name)
        if result.failed:
            failed.append(original_file_name)
            continue
        file_location = 'uploads/' + month + '/' + file_name
        number_uploaded += 1
        db.TblPhotos.insert(photo_path=file_location,
                            original_file_name=original_file_name,
                            Name=original_file_name,
                            uploader=user_id,
                            upload_date=datetime.datetime.now(),
                            width=result.width,
                            height=result.height,
                            crc=crc,
                            oversize=result.oversize,
                            photo_missing=False
                            )
    return dict(number_uploaded=number_uploaded, number_duplicates=number_duplicates, failed=failed)

def get_member_names(visible_only=None, gender=None):
    q = (db.TblMembers.id > 0)
    if visible_only:
        q &= (db.TblMembers.visible == True)
    if gender:
        q &= (db.TblMembers.gender == gender)

    lst = db(q).select()
    arr = [Storage(id=rec.id,
                   name=member_display_name(rec, full=True),
                   gender=rec.gender,
                   has_profile_photo=bool(rec.facePhotoURL),
                   facePhotoURL=photos_folder('profile_photos') + rec.facePhotoURL if rec.facePhotoURL else 'http://' + request.env.http_host  + "/gbs/static/images/dummy_face.png") for rec in lst]
    return arr

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

def get_member_rec(member_id, member_rec=None, prepend_path=False):
    if member_rec:
        rec = member_rec #used when initially all members are loaded into the cache
    elif not member_id:
        return None
    else:
        recs = db(db.TblMembers.id==member_id).select()
        rec = recs.render(0)
        rec = db(db.TblMembers.id==member_id).select().first()
    if not rec:
        return None
    rec = Storage(rec.as_dict())
    rec.full_name = member_display_name(rec, full=True)
    rec.name = member_display_name(rec, full=False)
    if prepend_path and rec.facePhotoURL:
        rec.facePhotoURL = photos_folder('profile_photos') + rec.facePhotoURL
    return rec

def get_parents(member_id):
    member_rec = get_member_rec(member_id)
    pa = member_rec.father_id
    ma = member_rec.mother_id
    pa_rec = get_member_rec(pa, prepend_path=True)
    ma_rec = get_member_rec(ma, prepend_path=True)
    parents = Storage()
    if pa_rec:
        parents.pa = pa_rec
    if ma_rec:
        parents.ma = ma_rec
    return parents

def get_siblings(member_id):
    parents = get_parents(member_id)
    if not parents:
        return []
    pa, ma = parents.pa, parents.ma
    q = db.TblMembers.id!=member_id
    if pa:
        lst1 = db(q & (db.TblMembers.father_id==pa.id)).select(orderby=db.TblMembers.date_of_birth) if pa else []
        lst1 = [r.id for r in lst1]
    else:
        lst1 = []
    if ma:
        lst2 = db(q & (db.TblMembers.mother_id==ma.id)).select(orderby=db.TblMembers.date_of_birth) if ma else []
        lst2 = [r.id for r in lst2]
    else:
        lst2 = []
    lst = list(set(lst1 + lst2)) #make it unique
    lst = [get_member_rec(id, prepend_path=True) for id in lst]
    lst = sorted(lst, key=lambda rec: rec.date_of_birth)
    return lst

def get_children(member_id):
    member_rec = get_member_rec(member_id)
    if member_rec.gender=='F' :
        q = db.TblMembers.mother_id==member_id
    elif member_rec.gender=='M':
        q = db.TblMembers.father_id==member_id
    else:
        return [] #error!
    lst = db(q).select(db.TblMembers.id, db.TblMembers.date_of_birth, orderby=db.TblMembers.date_of_birth)
    lst = [get_member_rec(rec.id, prepend_path=True) for rec in lst]
    return lst

def get_spouses(member_id):
    children = get_children(member_id)
    member_rec = get_member_rec(member_id)
    if member_rec.gender == 'F':
        spouses = [child.father_id for child in children]
    elif member_rec.gender == 'M':
        spouses = [child.mother_id for child in children]
    else:
        spouses = [] ##error
    spouses = [sp for sp in spouses if sp]  #to handle incomplete data
    visited = set([])
    spouses1 = []
    for sp_id in spouses:
        if sp_id in visited:
            continue
        else:
            visited |= set([sp_id])
            spouses1.append(sp_id)
    spouses = spouses1        
    ###spouses = list(set(spouses))  ## nice but does no preserve order
    return [get_member_rec(m_id, prepend_path=True) for m_id in spouses]

def get_family_connections(member_info):
    result = Storage(
        parents=get_parents(member_info.id),
        siblings=get_siblings(member_info.id),
        spouses=get_spouses(member_info.id),
        children=get_children(member_info.id)
    )
    result.hasFamilyConnections = len(result.parents) > 0 or len(result.siblings) > 0 or len(result.spouses) > 0 or len(result.children) > 0
    return result

def image_url(rec):
    #for development need full http address
    return photos_folder() + rec.TblPhotos.photo_path

def get_member_slides(member_id):
    q = (db.TblMemberPhotos.Member_id==member_id) & \
        (db.TblPhotos.id==db.TblMemberPhotos.Photo_id)
    return get_slides_from_photo_list(q)

def get_portrait_candidates(member_id): #todo: not in use
    q = (db.TblMemberPhotos.Member_id==member_id) & \
        (db.TblMemberPhotos.r > 10)
    lst = db(q).select(orderby=~db.TblMemberPhotos.r)
    return lst

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
def remove_face(vars):
    face = vars.face;
    if not face.member_id:
        return dict()
    q = (db.TblMemberPhotos.Photo_id==face.photo_id) & \
        (db.TblMemberPhotos.Member_id==face.member_id)
    good = db(q).delete() == 1
    return dict(face_deleted=good)

def get_photo_list_with_topics(vars):
    first = True
    for topic in vars.selected_topics:
        q = make_photos_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblPhotoTopics.photo_id==db.TblPhotos.id)
        q &= (db.TblTopics.id==db.TblPhotoTopics.topic_id)
        q &= (db.TblTopics.id==topic.id)
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

def date_of_partial_date(s):
    day = 1
    mon = 1
    year = None
    if not s:
        return None
    m = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', s)
    if m:
        day, mon, year = m.groups()
        day, mon, year = (int(day), int(mon), int(year))
    else:
        m = re.search(r'(\d{1,2})[./](\d{4})', s)
        if m:
            mon, year = m.groups()
            mon, year = (int(mon), int(year))
        else:
            m = re.search(r'(\d{4})', s)
            if m:
                year = int(m.groups()[0])
            else:
                raise User_Error("member.illgal-date")
    return datetime.date(year=year, month=mon, day=day)


def make_photos_query(vars):
    q = (db.TblPhotos.width > 0)
    #photographer_list = [p.id for p in vars.selected_photographers]
    #if len(photographer_list) > 0:
        #q1 = (db.TblPhotos.photographer_id == photographer_list[0])
        #for p in photographer_list[1:]:
            #q1 |= dbTblPhotos.photographer_id == p
        #q &= q1         
        ### q &= db.TblPhotos.photographer_id.belongs(photographer_list) caused error

    if vars.from_date:
        from_date = fix_date(vars.from_date)
        q &= (db.TblPhotos.photo_date >= from_date)
    if vars.to_date:
        to_date = fix_date(vars.to_date)
        q &= (db.TblPhotos.photo_date <= to_date)
    #if vars.selected_uploader:
        #q &= db.TblPhotos.uploader==vars.uploader
    if vars.selected_days_since_upload:
        days = vars.selected_days_since_upload.value
        if days:
            upload_date = datetime.date.today() - datetime.timedelta(days=days)
            q &= (db.TblPhotos.upload_date >= upload_date)
    return q

@serve_json
def get_photo_list(vars):
    if vars.selected_topics and len(vars.selected_topics) > 0:
        lst = get_photo_list_with_topics(vars)
    else:
        q = make_photos_query(vars)
        n = db(q).count()
        if n > MAX_PHOTOS_COUNT:
            frac = MAX_PHOTOS_COUNT * 100 / n
            sample = random.sample(range(1, 101), frac)
            ##q &= (db.TblPhotos.random_photo_key <= frac)
            q &= (db.TblPhotos.random_photo_key.belongs(sample)) #we don't want to bore our uses so there are several collections
        lst = db(q).select() ###, db.TblPhotographers.id) ##, db.TblPhotographers.id)
    if len(lst) > MAX_PHOTOS_COUNT:
        lst1 = random.sample(lst, MAX_PHOTOS_COUNT)
        lst = lst1
    result = []
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
            height=rec.height
        )
        result.append(dic)
    return dict(photo_list=result)

@serve_json
def get_topic_list(vars):
    topic_list = db(db.TblTopics).select(orderby=db.TblTopics.name)
    topic_list = [dict(name=rec.name, id=rec.id) for rec in topic_list if rec.name]
    #photographer_list = db(db.TblPhotographers).select(orderby=db.TblPhotographers.name)
    #photographer_list = [dict(name=rec.name, id=rec.id) for rec in photographer_list if rec.name]
    return dict(topic_list=topic_list) ###, photographer_list=photographer_list) 

@serve_json
def get_message_list(vars):
    q = (db.TblStories.used_for==STORY4MESSAGE)
    lst = db(q).select(orderby=~db.TblStories.creation_date, limitby=(0, vars.limit or 100))
    result = [dict(story_text=rec.TblStories.story, name=rec.TblStories.name, story_id=rec.TblStories.id) for rec in lst]
    return dict(message_list=result)

def fix_date(date_str):
    if date_str.endswith('-'):
        d = 1
        m = 1
        y = int(date_str[:-1])
    else:
        lst = re.split(r'[/.-]', date_str)
        lst = [int(s) for s in lst]
        if len(lst) == 3:
            if lst[2] > 1000:
                d, m, y = lst
            else:
                y, m, d = lst
        elif len(lst) == 2:
            d = 1
            m, y = lst
        else:
            d = 1
            m = 1
            y = int(lst[0])
            accuracy = 'Y'
    return datetime.date(day=d, month=m, year=y)

def save_profile_photo(face):
    rec = get_photo_rec(face.photo_id)
    input_path = local_photos_folder() + rec.photo_path
    facePhotoURL = "PP-{}-{}.jpg".format(face.member_id, face.photo_id)
    output_path = local_photos_folder("profile_photos") + facePhotoURL
    crop(input_path, output_path, face)
    db(db.TblMembers.id==face.member_id).update(facePhotoURL=facePhotoURL)
    return photos_folder("profile_photos") + facePhotoURL

def get_photo_rec(photo_id):
    rec = db(db.TblPhotos.id==photo_id).select().first()
    return rec

def save_story_data(story_info, used_for, user_id):
    story_id = story_info.story_id
    sm = stories_manager.Stories(user_id)
    if story_id:
        sm.update_story(story_id, story_info)
    else:
        story_id = sm.add_story(story_info, used_for=used_for)
    return story_id

def get_member_stories(member_id):
    q = (db.TblEventMembers.Member_id==member_id) & \
        (db.TblEventMembers.Event_id==db.TblEvents.id) & \
        (db.TblEvents.story_id==db.TblStories.id)
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
            creation_date=story.creation_date
        )
        result.append(dic)
    return result


