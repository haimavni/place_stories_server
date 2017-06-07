import stories_manager
from gluon.storage import Storage
from my_cache import Cache
import ws_messaging
from http_utils import json_to_storage
import datetime
import os
from dal_utils import insert_or_update
from photos import get_slides_from_photo_list, crop

def index():
    response.view = 'stories/main.html'
    return dict()

@serve_json
def get_item_list(vars):
    if vars.what == 'members':
        arr = get_member_names(vars.visible_only, vars.gender)
    elif vars.what == 'stories':
        arr = get_story_names()
    elif vars.what == 'terms':
        arr = get_term_names()
    elif vars.what == 'events':
        arr = get_event_names()
    elif vars.what == 'photos':
        arr = get_photo_names()
    else:
        return dict()
    index = dict()
    for i, rec in enumerate(arr):
        index[rec.id] = i
    return dict(arr=arr, index=index)

@serve_json
def member_names_json(vars):
    ###response.headers['Access-Control-Allow-Origin'] = '*'
    return dict(member_list=get_member_names(vars.visible_only, vars.gender))

@serve_json
def story_names_json(vars):
    return dict(story_list=get_story_names())

@serve_json
def term_names_json(vars):
    return dict(term_list=get_term_names())

@serve_json
def event_names_json(vars):
    return dict(event_list=get_event_names())

@serve_json
def get_member_info(vars):
    if not vars.member_id:
        raise User_Error(T('Member does not exist yet!'))
    #todo: vars can carry fields by which to sort the list and then
    #we must use the lines below, replacing the id by whatever

    #if vars.shift == 'next':
        #q = db.TblMembers.id>vars.member_id
    #elif vars.shift == 'prev':
        #q = db.TblMembers.id<vars.member_id
    #else:
        #q = db.TblMembers.id==vars.member_id
    #ob = ~db.TblMembers.id if vars.shift == 'prev' else db.TblMembers.id
    #member_info = db(q).select(limitby=(0, 1), orderby=ob).first()
    mem_id = int(vars.member_id)
    if vars.shift == 'next':
        mem_id += 1
    elif vars.shift == 'prev':
        mem_id -= 1
    #member_info = Storage(member_info.as_dict())
    member_info = get_member_rec(mem_id)
    if not member_info:
        raise User_Error(T('You reached the end of the list'))
    sm = stories_manager.Stories()
    story_info = sm.get_story(member_info.story_id) or Storage(display_version='New Story', story_versions=[], story_text='', story_id=None)
    family_connections = get_family_connections(member_info)
    slides = get_member_slides(mem_id)
    images = get_member_images(mem_id)
    return dict(member_info=member_info, story_info=story_info, family_connections=family_connections, images=images, slides=slides,
                dummy_face_path=request.application + '/static/images/dummy_face.png')

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
def get_term_info(vars):
    term_info = db(db.TblTerms.id==vars.term_id).select().first()
    sm = stories_manager.Stories()
    story_info = sm.get_story(term_info.story_id)
    return dict(term_info=term_info, story_info=story_info)

@serve_json
def get_event_info(vars):
    event_info = db(db.TblEvents.id==vars.event_id).select().first()
    sm = stories_manager.Stories()
    story_info = sm.get_story(event_info.story_id)
    return dict(event_info=event_info, story_info=story_info)

@serve_json
def get_story_info(vars):
    story_info = db(db.TblStories.id==vars.story_id).select().first()
    return dict(story_info=story_info)

@serve_json
def save_story(vars):
    story_info = vars.story_info
    story_text = story_info.story_text.replace('~1', '&').replace('~2', ';')
    story_id = story_info.story_id
    sm = stories_manager.Stories()
    if story_id:
        sm.update_story(story_id, story_text)
    else:
        story_id = sm.add_story(story_text, used_for=STORY4MEMBER)
    return dict(story_id=story_id)

@serve_json
def get_photo_info(vars):
    rec = get_photo_rec(vars.photo_id)
    rec.photo_url = 'gbs/static/gb_photos/' + rec.LocationInDisk
    sm = stories_manager.Stories()
    story_info = sm.get_story(rec.story_id)
    rec.name = rec.Name or story_info.name
    return dict(photo_info=rec, story_info=story_info)

@serve_json
def upload(vars):
    today = datetime.date.today()
    month = str(today)[:-3]
    path = 'applications/' + request.application + '/static/gb_photos/' + month + '/'
    if not os.path.isdir(path):
        os.makedirs(path)
    for fn in vars:
        fil = vars[fn]
        file_location = month + '/' + fil.filename
        with open(path + fil.filename, 'wb') as f:
            f.write(fil.value)
        db.TblPhotos.insert(LocationInDisk=file_location, 
                            uploader=auth.current_user(),
                            upload_date=datetime.datetime.now(),
                            width=0,
                            height=0,
                            photo_missing=False
                            )
    return dict(success=T('Files were uploaded succiessfuly'))

@serve_json
def read_chatroom(vars):
    messages = db(db.TblChats.chat_group==int(vars.room_number)).select()
    for msg in messages:
        msg.sender_name = auth.user_name(msg.author)
        msg.message = msg.message.replace('\n', '<br/>')
    chatroom_name = db(db.TblChatGroup.id==int(vars.room_number)).select().first().name
    return dict(chatroom_name=chatroom_name,
                messages=messages,
                user_message='')

@serve_json
def read_chatrooms(vars):
    lst = db(db.TblChatGroup).select()
    for rec in lst:
        rec.user_message = 'bla'
    dic = dict()
    for i, rec in enumerate(lst):
        dic[rec.id] = i
    return dict(chatrooms=lst, chatroom_index=dic)

@serve_json
def add_chatroom(vars):
    chatroom_id = db.TblChatGroup.insert(name=vars.new_chatroom_name,
                                         moderator_id=auth.current_user())
    return dict(chatroom_id=chatroom_id)

@serve_json
def send_message(vars):
    now = datetime.datetime.now()
    db.TblChats.insert(chat_group=int(vars.room_number),
                       author=auth.current_user(),
                       timestamp=now,
                       message=vars.user_message)
    ws_messaging.send_message(key='INCOMING_MESSAGE' + vars.room_number, 
                              group='CHATROOM' + vars.room_number,
                              author=auth.current_user(),
                              timestamp=str(now)[:19],
                              sender_name=auth.user_name(),
                              message=vars.user_message.replace('\n', '<br/>'))
    return dict(good=True)

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
def add_face(vars):
    face = vars.face
    face.r = face.r or 20
    data = dict(
        Photo_id=face.photo_id,
        r=face.r,
        x=face.x,
        y=face.y
    )
    db.TblMemberPhotos.insert(**data)
    return dict()

@serve_json
def resize_face(vars):
    face = vars.face
    q = (db.TblMemberPhotos.Photo_id==face.photo_id) & \
        (db.TblMemberPhotos.x==face.x) & \
        (db.TblMemberPhotos.y==face.y)
    assert(face.r > 0)
    if vars.resizing:
        db(q).update(r=face.r)
        return dict()
    assert(face.member_id > 0)
    if vars.make_profile_photo:
        save_profile_photo(face)
    db(q).update(Member_id=face.member_id)
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
 
#------------------------Support functions------------------------------

def save_story_info(story_info, used_for):
    story_text = story_info.story_text.replace('~1', '&').replace('~2', ';')
    story_id = story_info.story_id
    sm = stories_manager.Stories()
    if story_id:
        sm.update_story(story_id, story_text)
    else:
        story_id = sm.add_story(story_text, used_for=used_for)
    return story_id

def get_face_list(photo_id):
    lst = db(TblMemberPhotos.Photo_id==photo_id).select()

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
    s = rec.first_name
    if full and rec.former_first_name:
        s += ' ({})'.format(rec.former_first_name)
    s += ' ' + rec.last_name
    if full and rec.former_last_name:
        s += ' ({})'.format(rec.former_last_name)
    if rec.NickName:
        s += ' - {}'.format(rec.NickName)
    return s

def get_member_names(visible_only=None, gender=None, refresh=None):
    lst = db(db.TblMembers).select()
    arr = [Storage(id=rec.id, name=member_display_name(rec, full=False), full_name=member_display_name(rec, full=True), gender=rec.gender) for rec in lst]
    return arr

def get_story_names():
    q = (db.TblStories.id > 0) & (db.TblStories.name != None)  # & story usage
    lst = db(q).select(db.TblStories.id, db.TblStories.name, orderby=db.TblStories.name)
    arr = [Storage(id=rec.id, name=rec.name) for rec in lst]
    return arr

def get_term_names():
    q = (db.TblTerms.id > 0) & (db.TblTerms.Name != None)  # & story usage
    lst = db(q).select(db.TblTerms.id, db.TblTerms.Name, orderby=db.TblTerms.Name)
    arr = [Storage(id=rec.id, name=rec.Name) for rec in lst]
    return arr

def get_event_names():
    q = (db.TblEvents.id > 0) & (db.TblEvents.Name != None)  # & story usage
    lst = db(q).select(db.TblEvents.id, db.TblEvents.Name, orderby=db.TblEvents.Name)
    arr = [Storage(id=rec.id, name=rec.Name) for rec in lst]
    return arr

def get_photo_names():
    q = (db.TblPhotos.id > 0) & (db.TblPhotos.Name != None)
    lst = db(q).select(orderby=db.TblPhotos.Name)
    arr = [Storage(id=rec.id, name=rec.Name) for rec in lst]
    return arr

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
        return None
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
        return None #error!
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
    return Storage(
        parents=get_parents(member_info.id),
        siblings=get_siblings(member_info.id),
        spouses=get_spouses(member_info.id),
        children=get_children(member_info.id),
    )

def get_member_images(member_id):
    lst = db((db.TblMemberPhotos.Member_id==member_id) & \
             (db.TblPhotos.id==db.TblMemberPhotos.Photo_id) & \
             (db.TblPhotos.width>0)).select()
    return [dict(id=rec.TblPhotos.id, path=request.application + '/static/gb_photos/' + rec.TblPhotos.LocationInDisk) for rec in lst]

def get_member_slides(member_id):
    q = (db.TblMemberPhotos.Member_id==member_id) & \
        (db.TblPhotos.id==db.TblMemberPhotos.Photo_id)
    return get_slides_from_photo_list(q)

def get_photo_rec(photo_id):
    rec = db(db.TblPhotos.id==photo_id).select().first()
    return rec

def save_profile_photo(face):
    rec = get_photo_rec(face.photo_id)
    base_path = 'applications/' + request.application + '/static/gb_photos/'
    input_path = base_path + rec.LocationInDisk
    output_path = base_path + 'profile_photos/'
    output_path += "PP-{}.jpg".format(face.member_id)
    crop(input_path, output_path, face)
    db(db.TblMembers.id==face.member_id).update(has_profile_photo=True)

def test_stories():
    sm = stories_manager.Stories()
    s1 = '''
    hellow
    world
    '''
    s2 = '''
    hellow
    dear
    world
    '''
    s_id = sm.add_story(s1, 1)
    s = sm.get_story(s_id)
    sm.update_story(s_id, s2)
    s3 = sm.get_story(s_id)
    s4 = sm.get_story(s_id, story_version=0)
    return s4

