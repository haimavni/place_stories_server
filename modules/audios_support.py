from .injections import inject
import os
import datetime
from distutils import dir_util
import zlib
from gluon._compat import to_bytes
import array
from .date_utils import datetime_from_str
from gluon.storage import Storage
import random
import pwd
from .stories_manager import Stories
from .folders import url_folder, local_folder
from .pdf_utils import pdf_to_text, save_pdf_jpg
from time import sleep
from . import ws_messaging

def save_uploaded_audio(file_name, s, user_id, sub_folder=None):
    auth, log_exception, db, STORY4AUDIO = inject('auth', 'log_exception', 'db', 'STORY4AUDIO')
    user_id = user_id or auth.current_user()
    blob = to_bytes(s)
    crc = zlib.crc32(blob)
    cnt = db((db.TblAudios.crc == crc) & (db.TblAudios.deleted != True)).count()
    if cnt > 0:
        return 'duplicate'
    original_file_name, ext = os.path.splitext(file_name)
    file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
    today = datetime.date.today()
    month = str(today)[:-3]
    if not sub_folder:
        sub_folder = sub_folder or 'uploads/' + month + '/'
    path = local_audios_folder() + sub_folder
    audio_date = None
    dir_util.mkpath(path)
    audio_file_name = path + file_name
    blob = array.array('B', [x for x in map(ord, s)]).tobytes()
    try:
        path = local_audios_folder() + sub_folder
        with open(audio_file_name, 'wb') as f:
            f.write(blob)
    except Exception as e:
        log_exception("saving audio {} failed".format(original_file_name))
        return 'failed'
    sm = Stories()
    story_info = sm.get_empty_story(used_for=STORY4AUDIO, story_text="", name=original_file_name)
    result = sm.add_story(story_info)
    story_id = result.story_id
    audio_id = db.TblAudios.insert(
        audio_path=sub_folder + file_name,
        original_file_name=original_file_name,
        name=original_file_name,
        uploader=user_id,
        upload_date=datetime.datetime.now(),
        audio_date=audio_date,
        story_id=story_id,
        crc=crc,
        deleted=False
    )
    db.commit()
    return audio_id

def audios_folder(): 
    return url_folder('audios')

def local_audios_folder(): 
    return local_folder('audios')

def audio_url(story_id):
    db = inject('db')
    folder = audios_folder()
    rec = db(db.TblAudios.story_id==story_id).select().first()
    if not rec:
        return "Audio not found"
    path = folder + rec.audio_path
    return path

def audio_path(story_id):
    db = inject('db')
    folder = audios_folder()
    rec = db(db.TblAudios.story_id==story_id).select().first()
    if not rec:
        return "Audio not found"
    path = folder + rec.audio_path
    return path



