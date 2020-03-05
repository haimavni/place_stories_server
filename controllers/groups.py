from folders import *
import zlib
from cStringIO import StringIO
from PIL import Image, ImageFile
from photos_support import crop_to_square
from topics_support import *
import ws_messaging

@serve_json
def get_group_list(vars):
    lst = db(db.TblGroups.topic_id == db.TblTopics.id).select()
    lst = [dict(id=r.TblGroups.id, title=r.TblTopics.name, description=r.TblGroups.description, logo_url=get_logo_url(r.TblGroups.id)) for r in lst]
    return dict(group_list = lst)

@serve_json
def add_or_update_group(vars):
    group_id = vars.id
    if group_id:
        rec = db(db.TblGroups.id==group_id).select().first()
        rename_a_topic(rec.topic_id, vars.title) 
        rec.update_record(description=vars.description)
        #todo: rename topic! (or use only topic_id)
    else:
        topic_id = add_a_topic(vars.title)
        group_id = db.TblGroups.insert(topic_id=topic_id, description=vars.description)
    group_data = dict(title=vars.title, description=vars.description,id=group_id)
    return dict(group_data=group_data)

@serve_json
def get_group_info(vars):
    group_id = vars.group_id
    logo_url = get_logo_url(group_id)
    rec = db(db.TblGroups.id==group_id).select().first()
    result = dict(title=topic_name(rec.topic_id),
                  description=rec.description,
                  logo_url=logo_url)
    
@serve_json
def upload_logo(vars):
    fil = vars.file
    group_id=fil.info.group_id
    file_name = save_uploaded_logo(fil.name, fil.BINvalue, group_id)
    return dict(upload_result=dict(), logo_url=get_logo_url(group_id))

@serve_json
def delete_group(vars):
    db(db.TblGroups.id==vars.group_id).delete()
    return dict()

#-----------support functions----------------------------
       
def get_logo_url(group_id):
    rec = db(db.TblGroups.id==group_id).select().first()
    folder = url_folder('logos')
    logo_name = rec.logo_name if rec.logo_name else 'dummy-logo.jpg'
    return folder + logo_name
    
def save_uploaded_logo(file_name, blob, group_id):
    crc = zlib.crc32(blob)
    original_file_name, ext = os.path.splitext(file_name)
    file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
    path = local_folder('logos')
    dir_util.mkpath(path)
    stream = StringIO(blob)
    img = Image.open(stream)
    width, height = img.size
    img = crop_to_square(img, width, height, 256)
    img.save(path + file_name)
    db(db.TblGroups.id==group_id).update(logo_name=file_name)
    ws_messaging.send_message(key='GROUP-LOGO-UPLOADED', group='ALL', group_id=group_id, logo_url=get_logo_url(group_id))
    return file_name
