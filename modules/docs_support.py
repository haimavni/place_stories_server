from .injections import inject
import os
import datetime
from distutils import dir_util
import zlib
from .date_utils import datetime_from_str
from gluon.storage import Storage
import random
from .stories_manager import Stories
from .folders import url_folder, local_folder
from .pdf_utils import pdf_to_text, save_pdf_jpg
from time import sleep
from . import ws_messaging
from misc_utils import chmod, timestamp
import array

def create_uploading_doc(file_name, crc, user_id):
    auth, log_exception, db, STORY4DOC = inject('auth', 'log_exception', 'db', 'STORY4DOC')
    user_id = user_id or auth.current_user()
    record_id = db((db.TblDocs.crc == crc) & (db.TblDocs.deleted != True)).select().first()
    if record_id:
        return Storage(duplicate=record_id)
    original_file_name, ext = os.path.splitext(file_name)
    file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
    today = datetime.date.today()
    month = str(today)[:-3]
    sub_folder = 'uploads/' + month + '/'
    path = local_docs_folder() + sub_folder
    doc_date = None
    dir_util.mkpath(path)
    doc_file_name = path + file_name
    with open(path + file_name, 'wb') as f:
        pass
    sm = Stories()
    story_info = sm.get_empty_story(used_for=STORY4DOC, story_text="", name=original_file_name)
    result = sm.add_story(story_info)
    story_id = result.story_id
    record_id = db.TblDocs.insert(
        doc_path=sub_folder + file_name,
        original_file_name=original_file_name,
        name=original_file_name,
        crc=crc,
        story_id=story_id,
        uploader=user_id,
        deleted=False,
        upload_date=datetime.datetime.now()
    )
    return Storage(record_id=record_id)


def save_uploading_chunk(record_id, start, blob):
    db, comment = inject('db', 'comment')
    # comment(f"save_uploading_chunk. record id: {record_id}, start: {start}")
    drec = db(db.TblDocs.id==record_id).select().first()
    if not drec:
        raise Exception(f'record_id {record_id} not found')
    file_name = local_docs_folder() + drec.doc_path
    # comment(f"save_uploading_chunk. file_name: {file_name}, record id: {record_id}, start: {start}")
    with open(file_name, 'ab') as f:
        f.seek(start, 0)
        f.tell()
        f.write(blob)
        f.flush()


def handle_loaded_doc(record_id):
    db = inject('db')
    drec = db(db.TblDocs.id==record_id).select().first()
    path, file_name = os.path.split(drec.doc_path)
    doc_file_name = local_docs_folder() + drec.doc_path
    pdf_jpg_folder = local_docs_folder() + 'pdf_jpgs/' + path + '/'
    dir_util.mkpath(pdf_jpg_folder)
    pdf_jpg_path = pdf_jpg_folder + file_name.replace('.pdf', '.jpg')
    save_pdf_jpg(doc_file_name, pdf_jpg_path)
    chmod(pdf_jpg_path, 0o777)

def save_doc_segment_thumbnail(doc_segment_id):
    # save using pdf2image which does not always works
    db, comment = inject('db', 'comment')
    pdf_seg_rec = db(db.TblDocSegments.id==doc_segment_id).select().first()
    doc_rec = db(db.TblDocs.id==pdf_seg_rec.doc_id).select().first()
    doc_file_name = local_docs_folder() + doc_rec.doc_path
    #-------
    pdf_jpg_path = get_pdf_jpg_path(doc_rec.doc_path, pdf_seg_rec.page_num)
    comment(f"-----save doc seg thumb {doc_file_name} at {pdf_jpg_path} ")
    save_pdf_jpg(doc_file_name, pdf_jpg_path, pdf_seg_rec.page_num)
    chmod(pdf_jpg_path, 0o777)

def save_uploaded_doc_seg_thumbnail(data, doc_id, segment_id, ptp_key):
    #sometimes the above function silently fails to create file
    db, comment = inject('db', 'comment')
    # comment(f"------------ save uploaded thumbail {doc_id} / {segment_id}")
    blob = array.array('B', [x for x in map(ord, data)]).tobytes()
    doc_rec = db(db.TblDocs.id==doc_id).select().first()
    page_num = None
    if segment_id:
        doc_seg_rec = db(db.TblDocSegments.id==segment_id).select().first()
        page_num = doc_seg_rec.page_num
    pdf_jpg_path = get_pdf_jpg_path(doc_rec.doc_path, page_num)
    # comment(f"pdf_jpg_path: {pdf_jpg_path}")
    with open(pdf_jpg_path, "bw") as f:
        f.write(blob)
    chmod(pdf_jpg_path, 0o777)
    return True

def save_uploaded_doc_thumbnail(data, doc_id, ptp_key):
    #sometimes the above function silently fails to create file
    db, comment = inject('db', 'comment')
    # comment(f"------------ save uploaded doc thumbail {doc_id} ptp key: {ptp_key}")
    blob = array.array('B', [x for x in map(ord, data)]).tobytes()
    # doc_rec = db(db.TblDocs.id==doc_id).select().first()
    pdf_jpg_path = calc_doc_jpg_path(doc_id)
    # comment(f"pdf_jpg_path: {pdf_jpg_path}")
    if os.path.exists(pdf_jpg_path):
        os.rename(pdf_jpg_path, pdf_jpg_path + ".bak")
    with open(pdf_jpg_path, "bw") as f:
        f.write(blob)
    chmod(pdf_jpg_path, 0o777)
    return True

def restore_doc_thumbnail(doc_id):
    db, comment = inject('db', 'comment')
    pdf_jpg_path = calc_doc_jpg_path(doc_id)
    bak_path = pdf_jpg_path + ".bak"
    if os.path.exists(bak_path):
        os.remove(pdf_jpg_path)
        os.rename(bak_path, pdf_jpg_path)
    
def confirm_doc_thumbnail(doc_id):
    db, comment = inject('db', 'comment')
    pdf_jpg_path = calc_doc_jpg_path(doc_id)
    bak_path = pdf_jpg_path + ".bak"
    if os.path.exists(bak_path):
        os.remove(bak_path)

def calc_doc_jpg_path(doc_id):
    db, comment = inject('db', 'comment')
    doc_rec = db(db.TblDocs.id==doc_id).select().first()
    return get_pdf_jpg_path(doc_rec.doc_path)

def get_pdf_jpg_path(doc_path, page_num=None):    
    path, file_name = os.path.split(doc_path)
    pdf_jpg_folder = local_docs_folder() + 'pdf_jpgs/' + path + '/'
    dir_util.mkpath(pdf_jpg_folder)
    s = f"-{page_num}.jpg" if page_num else ".jpg"
    result = pdf_jpg_folder + file_name.replace('.pdf', s)
    return result

# code below is obsolete??
def save_uploaded_doc(file_name, data, user_id, sub_folder=None):
    auth, log_exception, db, STORY4DOC = inject('auth', 'log_exception', 'db', 'STORY4DOC')
    user_id = user_id or auth.current_user()
    blob = array.array('B', [x for x in map(ord, data)]).tobytes()
    crc = zlib.crc32(blob)
    cnt = db((db.TblDocs.crc == crc) & (db.TblDocs.deleted != True)).count()
    if cnt > 0:
        return 'duplicate'
    original_file_name, ext = os.path.splitext(file_name)
    file_name = '{crc:x}{ext}'.format(crc=crc & 0xffffffff, ext=ext)
    today = datetime.date.today()
    month = str(today)[:-3]
    if not sub_folder:
        sub_folder = 'uploads/' + month + '/'
    path = local_docs_folder() + sub_folder
    doc_date = None
    dir_util.mkpath(path)
    doc_file_name = path + file_name
    try:
        path = local_docs_folder() + sub_folder
        with open(doc_file_name, 'wb') as f:
            f.write(blob)
    except Exception as e:
        log_exception("saving doc {} failed".format(original_file_name))
        return 'failed'
    sm = Stories()
    story_info = sm.get_empty_story(used_for=STORY4DOC, story_text="", name=original_file_name)
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
        story_id=story_id,
        deleted=False
    )
    pdf_jpg_folder = local_docs_folder() + 'pdf_jpgs/' + sub_folder
    dir_util.mkpath(pdf_jpg_folder)
    pdf_jpg_path = pdf_jpg_folder + file_name.replace('.pdf', '.jpg')
    save_pdf_jpg(doc_file_name, pdf_jpg_path)
    db.commit()
    return doc_id

def generate_jpgs_for_all_pdfs():
    db = inject('db')
    q = db.TblDocs.deleted != True
    lst = db(q).select()
    pdf_jpg_folder = local_docs_folder() + 'pdf_jpgs/'
    dir_util.mkpath(pdf_jpg_folder)
    for rec in lst:
        pdf_path = local_docs_folder() + rec.doc_path
        if not os.path.isfile(pdf_path):
            continue
        jpg_path = pdf_path.replace('/docs/', '/docs/pdf_jpgs/').replace('.pdf', '.jpg')
        # r = jpg_path.rfind('/')
        # p = jpg_path[:r+1]
        # dir_util.mkpath(p)
        # jpg_path = pdf_jpg_folder + rec.doc_path.replace('.pdf', '.jpg')
        save_pdf_jpg(pdf_path, jpg_path)
    return len(lst)

def generate_jpgs_for_all_pdf_segmements():
    db = inject('db')
    q = (db.TblDocSegments.story_id==db.TblStories.id) & \
        (db.TblStories.deleted != True) & \
        (db.TblDocs.id==db.TblDocSegments.doc_id)
    lst = db(q).select()
    pdf_jpg_folder = local_docs_folder() + 'pdf_jpgs/'
    dir_util.mkpath(pdf_jpg_folder)
    for rec in lst:
        pdf_path = local_docs_folder() + rec.TblDocs.doc_path
        if not os.path.isfile(pdf_path):
            continue
        page_num = rec.TblDocSegments.page_num
        jpg_path = pdf_path.replace('/docs/', '/docs/pdf_jpgs/').replace('.pdf', f"-{page_num}.jpg")
        # r = jpg_path.rfind('/')
        # p = jpg_path[:r+1]
        # dir_util.mkpath(p)
        # jpg_path = pdf_jpg_folder + rec.doc_path.replace('.pdf', '.jpg')
        save_pdf_jpg(pdf_path, jpg_path, page_num=page_num)
    return len(lst)

def docs_folder(): 
    return url_folder('docs')

def local_docs_folder(): 
    return local_folder('docs')

def doc_url(story_id, drec=None):
    db = inject("db")
    if not drec:
        drec = db(db.TblDocs.story_id==story_id).select().first()
    folder = docs_folder()
    return folder + drec.doc_path

def doc_jpg_url(story_id, drec=None):
    db = inject("db")
    if not drec:
        drec = db(db.TblDocs.story_id==story_id).select().first()
    folder = docs_folder() + "pdf_jpgs/"
    jpg_path =  drec.doc_path.replace(".pdf", ".jpg")
    local_fname = local_docs_folder() + "pdf_jpgs/" + jpg_path
    return folder + jpg_path + timestamp(local_fname)

def doc_segment_url(story_id, rec=None):
    if not rec:
        rec = doc_segment_by_story_id(story_id)
    if not rec:
        return None
    doc_rec = rec.TblDocs
    seg_rec = rec.TblDocSegments
    folder = docs_folder()
    return folder + doc_rec.doc_path

def doc_segment_jpg_url(story_id, rec=None):
    if not rec:
        rec = doc_segment_by_story_id(story_id)
    if not rec:
        return None
    doc_rec = rec.TblDocs
    seg_rec = rec.TblDocSegments
    path = doc_rec.doc_path.replace(".pdf", f"-{seg_rec.page_num}.jpg")
    folder = docs_folder() + "pdf_jpgs/"
    local_folder = local_docs_folder() + "pdf_jpgs/"
    local_path = local_folder + path
    return folder + path + timestamp(local_path)

def doc_segment_by_story_id(story_id):
    db = inject("db")
    q = (db.TblDocSegments.story_id==story_id) & \
        (db.TblDocs.id==db.TblDocSegments.doc_id)
    rec = db(q).select().first()
    return rec
