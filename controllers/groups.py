from folders import *
import zlib
from cStringIO import StringIO
from PIL import Image, ImageFile
from photos_support import crop_to_square

@serve_json
def get_group_list(vars):
    lst = db(db.TblGroups.deleted != True).select()
    lst = [dict(id=r.id, title=r.title, description=r.description, logo_url=get_logo_url(r.id)) for r in lst]
    return dict(group_list = lst)

@serve_json
def add_or_update_group(vars):
    data = dict(title=vars.title, description=vars.description)
    if vars.group_id:
        rec = db(db.TblGroups.id==vars.group_id).select().first()
        rec.update_record(**data)
    else:
        if not db(db.TblGroups.title==vars.title).isempty():
            raise User_Error('groups.duplicate')
        group_id = db.TblGroups.insert(**data)
    return dict(group_id=group_id)

@serve_json
def get_group_info(vars):
    group_id = vars.group_id
    logo_url = get_logo_url(group_id)
    rec = db(db.TblGroups.id==group_id).select().first()
    result = dict(title=rec.title,
                  description=rec.description,
                  logo_url=logo_url)
    
@serve_json
def upload_logo(vars):
    fil = vars.file
    group_id=fil.info.group_id
    file_name = save_uploaded_logo(fil.name, fil.BINvalue, group_id)
    return dict(logo_url=get_logo_url(group_id))

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
    return file_name
