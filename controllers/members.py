import stories_manager
from gluon.storage import Storage
from my_cache import Cache
import ws_messaging
from http_utils import json_to_storage
import datetime
import os
from dal_utils import insert_or_update
from photos import get_slides_from_photo_list, photos_folder, local_photos_folder, crop
import random

@serve_json
def member_list(vars):
    return dict(member_list=get_member_names(vars.visible_only, vars.gender))

@serve_json
def get_member_details(vars):
    if not vars.member_id:
        raise User_Error(T('Member does not exist yet!'))
    if vars.member_id == "new":
        new_member = dict(
            member_info=Storage(
                first_name="",
                last_name="",
                former_first_name="",
                former_last_name="",
                full_name="members.new-member"),
            story_info = Storage(display_version='New Story', story_versions=[], story_text='', story_id=None),
            family_connections =  Storage(
                parents=dict(pa=None, ma=None),
                siblings=[],
                spouses=[],
                children=[]
            ),
            images = [],
            slides=[],
            spouses=[],
            facePhotoURL = request.application + '/static/images/dummy_face.png'
        )
        return new_member
    mem_id = int(vars.member_id)
    if vars.shift == 'next':
        mem_id += 1
    elif vars.shift == 'prev':
        mem_id -= 1
    member_info = get_member_rec(mem_id)
    if not member_info:
        raise User_Error(T('You reached the end of the list'))
    sm = stories_manager.Stories()
    story_info = sm.get_story(member_info.story_id) or Storage(display_version='New Story', story_versions=[], story_text='', story_id=None)
    family_connections = get_family_connections(member_info)
    slides = get_member_slides(mem_id)
    if member_info.gender == 'F':
        spouses = 'husband' + ('s' if len(family_connections.spouses) > 1 else '')
    else:
        spouses = 'wife' + ('s' if len(family_connections.spouses) > 1 else '')
    return dict(member_info=member_info, story_info=story_info, family_connections=family_connections, 
                ##images=images,
                slides=slides, #todo: duplicate?
                spouses = spouses,
                facePhotoURL = member_info.facePhotoURL or request.application + '/static/images/dummy_face.png')

@serve_json
def save_member_details(vars):
    member_info = vars.member_info
    new_member = member_info.id == "new" or not member_info.id
    result = insert_or_update(db.TblMembers, **member_info)
    if isinstance(result, dict):
        return dict(errors=result['errors'])
    mem_id = result
    member_rec = get_member_rec(mem_id)
    member_rec = json_to_storage(member_rec)
    ws_messaging.send_message(key='MEMBER_LISTS_CHANGED', group='ALL_USERS', member_rec=member_rec, new_member=new_member);

    return dict(success=T('Data saved successfuly'))

@serve_json
def save_member_info(vars):
    story_info = vars.story_info
    if story_info:
        story_id = save_story_info(story_info, used_for=STORY4MEMBER)
    else:
        story_id = None
    member_id = vars.member_id
    member_info = vars.member_info
    if member_info:
        new_member = not member_info.id
        if story_id:
            member_info.story_id = story_id
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
    today = datetime.date.today()
    month = str(today)[:-3]

    path = local_photos_folder() + month + '/'
    if not os.path.isdir(path):
        os.makedirs(path)
    for fn in vars:
        fil = vars[fn]
        file_location = month + '/' + fil.name
        with open(path + fil.name, 'wb') as f:
            f.write(fil.BINvalue)
        db.TblPhotos.insert(LocationInDisk=file_location, 
                            uploader=auth.current_user(),
                            upload_date=datetime.datetime.now(),
                            width=0,
                            height=0,
                            photo_missing=False
                            )
    return dict(success='files-loaded-successfuly')

def get_member_names(visible_only=None, gender=None):
    q = (db.TblMembers.id > 0)
    if visible_only:
        q &= (db.TblMembers.visible == True)
    if gender:
        q &= (db.TblMembers.gender == gender)

    lst = db(q).select(db.TblMembers.first_name,
                       db.TblMembers.last_name,
                       db.TblMembers.former_first_name,
                       db.TblMembers.former_last_name,
                       db.TblMembers.NickName,
                       db.TblMembers.gender,
                       db.TblMembers.visible,
                       db.TblMembers.facePhotoURL,
                       orderby=[db.TblMembers.last_name, db.TblMembers.first_name])
    arr = [Storage(id=rec.id,
                   name=member_display_name(rec, full=True),
                   gender=rec.gender,
                   facePhotoURL=rec.facePhotoURL or 'http://' + request.env.http_host + "/gbs/static/images/dummy_face.png") for rec in lst]
    return arr

def get_member_names(visible_only=None, gender=None):
    q = (db.TblMembers.id > 0)
    if visible_only:
        q &= (db.TblMembers.visible == True)
    if gender:
        q &= (db.TblMembers.gender == gender)

    lst = db(q).select()
    face_photo_url = 'http://' + request.env.http_host + '/' + photos_folder('profile_photos') +'PP-'
    arr = [Storage(id=rec.id,
                   name=member_display_name(rec, full=True),
                   gender=rec.gender,
                   has_profile_photo=rec.has_profile_photo,
                   facePhotoURL=face_photo_url + str(rec.id) + ".jpg" if rec.has_profile_photo else 'http://' + request.env.http_host  + "/gbs/static/images/dummy_face.png") for rec in lst]
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

def get_member_rec(member_id, member_rec=None):
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
    return rec

def get_parents(member_id):
    member_rec = get_member_rec(member_id)
    pa = member_rec.father_id
    ma = member_rec.mother_id
    pa_rec = get_member_rec(pa)
    ma_rec = get_member_rec(ma)
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
        lst1 = db(q & (db.TblMembers.father_id==pa.id)).select() if pa else []
        lst1 = [r.id for r in lst1]
    else:
        lst1 = []
    if ma:
        lst2 = db(q & (db.TblMembers.mother_id==ma.id)).select() if ma else []
        lst2 = [r.id for r in lst2]
    else:
        lst2 = []
    lst = list(set(lst1 + lst2)) #make it unique
    lst = [get_member_rec(id) for id in lst]
    return lst

def get_children(member_id):
    member_rec = get_member_rec(member_id)
    if member_rec.gender=='F' :
        q = db.TblMembers.mother_id==member_id
    elif member_rec.gender=='M':
        q = db.TblMembers.father_id==member_id
    else:
        return [] #error!
    lst = db(q).select(db.TblMembers.id)
    lst = [get_member_rec(rec.id) for rec in lst]
    return lst
    ###return [Storage(rec.as_dict()) for rec in lst] more efficient but not as safe

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
    spouses = list(set(spouses))
    return [get_member_rec(m_id) for m_id in spouses]

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
    return 'http://' + request.env.http_host + '/gbs/static/' + photos_folder() + rec.TblPhotos.LocationInDisk

def get_member_slides(member_id):
    q = (db.TblMemberPhotos.Member_id==member_id) & \
        (db.TblPhotos.id==db.TblMemberPhotos.Photo_id)
    return get_slides_from_photo_list(q)

def get_portrait_candidates(member_id):
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
        if rec.r == None: #found old record which has a memeber but no location
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
    return dict(faces=faces, candidates=candidates)

@serve_json
def save_face(vars):
    face = vars.face    
    assert(face.member_id > 0)
    if vars.make_profile_photo:
        save_profile_photo(face)
    q = (db.TblMemberPhotos.Photo_id==face.photo_id) & \
        (db.TblMemberPhotos.Member_id==face.member_id)
    data = dict(
        Photo_id=face.photo_id,
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
    return dict(member_name=member_name)
    
@serve_json
def remove_face(vars):
    face = vars.face;
    if not face.member_id:
        return dict()
    q = (db.TblMemberPhotos.Photo_id==face.photo_id) & \
        (db.TblMemberPhotos.Member_id==face.member_id)
    good = db(q).delete() == 1
    return dict(face_deleted=good)

@serve_json
def get_photos_list(vars):
    q = (db.TblPhotos.width > 0)
    if vars.uploader:
        q &= db.TblPhotos.uploader==vars.uploader
    if vars.uploaded_since:
        upload_date = datetime.datetime.now() - datetime.timedelta(days=vars.uploaded_since)
        q &= db.TblPhotos.upload_date > upload_date
    if vars.after:
        q &= db.TblPhotos.photo_date > vars.after
    if vars.before:
        q &= db.TblPhotos.photo_date < vars.before
    if vars.photographer_id:
        q &= db.TblPhotos.photographer_id == photographer_id
    if vars.keywords:
        keywords = vars.keywords.split()
        for kw in keywords:
            q &= db.TblPhotos.KeyWords.like(kw)
    ###q &= db.TblPhotos.photographer_id==db.TblPhotographers.id
    lst = db(q).select(db.TblPhotos.KeyWords, db.TblPhotos.photo_date, db.TblPhotos.photo_date_accuracy, db.TblPhotos.LocationInDisk) ###, db.TblPhotographers.id) ##, db.TblPhotographers.id)
    if len(lst) > 1000:
        lst1 = random.sample(lst, 1000)
        lst = lst1
    result = []
    for r in lst:
        dic = dict(
            keywords = r.KeyWords,
            src = photos_folder('squares') + r.LocationInDisk
        )
        result.append(dic)
    return dict(photo_list=result)
        

def save_profile_photo(face):
    rec = get_photo_rec(face.photo_id)
    input_path = local_photos_folder() + rec.LocationInDisk
    output_path = local_photos_folder("profile_photos") + "PP-{}.jpg".format(face.member_id)
    crop(input_path, output_path, face)
    db(db.TblMembers.id==face.member_id).update(has_profile_photo=True)
    
def get_photo_rec(photo_id):
    rec = db(db.TblPhotos.id==photo_id).select().first()
    return rec

def save_story_info(story_info, used_for):
    story_text = story_info.story_text.replace('~1', '&').replace('~2', ';')
    story_id = story_info.story_id
    sm = stories_manager.Stories()
    if story_id:
        sm.update_story(story_id, story_text)
    else:
        story_id = sm.add_story(story_text, used_for=used_for)
    return story_id

    

