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
from pdf_utils import pdf_to_text
from time import sleep
import ws_messaging

def save_uploaded_doc(file_name, blob, user_id, sub_folder=None):
    auth, log_exception, db, STORY4DOC = inject('auth', 'log_exception', 'db', 'STORY4DOC')
    user_id = user_id or auth.current_user()
    crc = zlib.crc32(blob)
    cnt = db((db.TblDocs.crc == crc) & (db.TblDocs.deleted != True)).count()
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
    doc_id = db.TblDocs.insert(
        doc_path=sub_folder + file_name,
        original_file_name=original_file_name,
        name=original_file_name,
        uploader=user_id,
        upload_date=datetime.datetime.now(),
        doc_date=doc_date,
        crc=crc,
        deleted=False
    )
    db.commit()
    return doc_id

def calc_doc_story(doc_id):
    try:
        db, STORY4DOC, log_exception, comment = inject('db', 'STORY4DOC', 'log_exception', 'comment')
        doc_rec = db(db.TblDocs.id==doc_id).select().first()
        doc_file_name = local_docs_folder() + doc_rec.doc_path
        sm = Stories()
        good = True
        try:
            txt = pdf_to_text(doc_file_name)
        except Exception, e:
            log_exception('PDF to text error in {}. Name: {}'.format(doc_rec.doc_path, doc_rec.original_file_name))
            txt = 'Failed to extract text from this document'
            good = False
        if not txt:
            txt = '- - -'
        story_info = sm.get_empty_story(used_for=STORY4DOC, story_text=txt, name=doc_rec.original_file_name)
        result = sm.add_story(story_info)
        story_id = result.story_id
        doc_rec.update_record(story_id=story_id)
    except Exception, e:
        log_exception('Error calculating {}'.format(doc_rec.doc_path))
        return False
    return good
    
def calc_doc_stories(time_budget=None):
    db, comment, log_exception = inject('db', 'comment', 'log_exception')
    chunk = 10
    comment("Start calc doc stories cycle")
    q = (db.TblDocs.story_id == None) & (db.TblDocs.deleted != True)
    n = db(q).count()
    comment('Start calc doc stories. {} documents left to calculate.', n)
    time_budget = time_budget or (2 * 3600 - 25) #will exit the loop 25 seconds before the a new cycle starts
    t0 = datetime.datetime.now()
    ns = 0
    nf = 0
    try:
        while True:
            dif = datetime.datetime.now() - t0
            elapsed = int(dif.total_seconds())
            if elapsed > time_budget:
                break
            n = db(q).count()
            doc_ids = []
            if n > 0:
                comment('Calc doc stories. {} documents left to calculate.', n)
                lst = db(q).select(db.TblDocs.id, limitby=(0, chunk))
                for rec in lst:
                    if calc_doc_story(rec.id):
                        doc_ids.append(rec.id)
                        ns += 1
                    else:
                        nf += 1
                db.commit()
                comment("{} good, {} bad uploaded", ns, nf)
                ws_messaging.send_message('DOCS_WERE_UPLOADED', group='ALL', doc_ids=doc_ids)
            else:
                sleep(5)
    except:
        log_exception('Error while calculating doc stories')
    finally:
        comment("Finished cycle of calculating doc stories")
    return dict(good=ns, bad=nf)

def docs_folder(): 
    return url_folder('docs')

def local_docs_folder(): 
    return local_folder('docs')

def doc_url(story_id):
    db = inject('db')
    folder = docs_folder()
    rec = db(db.TblDocs.story_id==story_id).select().first()
    if not rec:
        return "Document not found"
    path = folder + rec.doc_path
    return path


