import stories_manager
from gluon.storage import Storage
from my_cache import Cache
import ws_messaging
from http_utils import json_to_storage
import datetime
import os
from dal_utils import insert_or_update
from photos_support import photos_folder, timestamped_photo_path

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
    story_text = story_info.story_text
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
    rec.photo_url = photos_folder() + timestamped_photo_path(rec)
    sm = stories_manager.Stories()
    story_info = sm.get_story(rec.story_id)
    rec.name = rec.Name or story_info.name
    return dict(photo_info=rec, story_info=story_info)

@serve_json
def upload(vars):
    today = datetime.date.today()
    month = str(today)[:-3]

    path = local_photos_folder() + month + '/'
    if not os.path.isdir(path):
        os.makedirs(path)
    for fn in vars:
        fil = vars[fn]
        file_location = month + '/' + fil.filename
        with open(path + fil.filename, 'wb') as f:
            f.write(fil.value)
        db.TblPhotos.insert(photo_path=file_location, 
                            uploader=auth.current_user(),
                            upload_date=datetime.datetime.now(),
                            width=0,
                            height=0,
                            photo_missing=False,
                            deleted=False
                            )
    return dict(success='files-loaded-successfuly')

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

#------------------------Support functions------------------------------

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
    q = (db.TblPhotos.id > 0) & (db.TblPhotos.Name != None) & (db.TblPhotos.deleted!=True)
    lst = db(q).select(orderby=db.TblPhotos.Name)
    arr = [Storage(id=rec.id, name=rec.Name) for rec in lst]
    return arr

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

