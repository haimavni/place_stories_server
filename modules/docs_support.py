from injections import inject
import os
import datetime
from distutils import dir_util
import zlib
from date_utils import datetime_from_str
from gluon.storage import Storage
import random
import pwd
from stories_manager import Stories
from folders import url_folder, local_folder
from pdf2text import pdf_to_text

def save_uploaded_doc(file_name, blob, user_id, sub_folder=None):
    auth, log_exception, db, STORY4DOC = inject('auth', 'log_exception', 'db', 'STORY4DOC')
    user_id = user_id or auth.current_user()
    crc = zlib.crc32(blob)
    cnt = db(db.TblDocs.crc==crc).count()
    if cnt > 0:
        return 'duplicate'
    original_file_name, ext = os.path.splitext(file_name)
    file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
    today = datetime.date.today()
    month = str(today)[:-3]
    if not sub_folder:
        sub_folder = sub_folder or 'uploads/' + month + '/'
    path = local_docs_folder() + sub_folder
    doc_date = None
    dir_util.mkpath(path)
    doc_file_name = path + file_name
    try:
        path = local_docs_folder() + sub_folder
        with open(doc_file_name, 'w') as f:
            f.write(blob)
    except Exception, e:
        log_exception("saving doc {} failed".format(original_file_name))
        return 'failed'
    sm = Stories()
    txt = pdf_to_text(doc_file_name)
    story_info = sm.get_empty_story(used_for=STORY4DOC, story_text=txt, name=original_file_name)
    result = sm.add_story(story_info)
    story_id = result.story_id
    doc_id = db.TblDocs.insert(
        doc_path=sub_folder + file_name,
        original_file_name=original_file_name,
        name=original_file_name,
        uploader=user_id,
        upload_date=datetime.datetime.now(),
        doc_date=doc_date,
        crc=crc,
        deleted=False,
        story_id=story_id
    )
    db.commit()
    n = db(db.TblDocs).count()
    return doc_id

def docs_folder(): 
    return url_folder('docs')

def local_docs_folder(): 
    return local_folder('docs')

