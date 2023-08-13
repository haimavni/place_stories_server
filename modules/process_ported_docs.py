from docs_support import save_pdf_jpg, local_docs_folder 
from injections import inject
from distutils import dir_util
import zlib
import os

class ProcessPortedDocs:
    def __init__(self):
        self.db, self.log_exception = inject("db", "log_exception")

    def log_it(self, s):
        my_log = inject("my_log")
        my_log(s, file_name="process_docs.log")

    def process_ported_doc(self, doc_id):
        db = self.db
        doc_rec = db(db.TblDocs.id==doc_id).select().first()
        fname = local_docs_folder() + doc_rec.doc_path
        with open(fname, 'rb') as f:
            blob = f.read()
        crc = zlib.crc32(blob)
        doc_rec.update_record(
            crc=crc
        )
        pdf_jpg_folder = local_docs_folder() + 'pdf_jpgs/' + doc_rec.doc_path
        dir_util.mkpath(pdf_jpg_folder)
        pdf_jpg_path = pdf_jpg_folder + fname.replace('.pdf', '.jpg')
        save_pdf_jpg(fname, pdf_jpg_path)
        db.commit()
        return doc_id
    
    def process_unprocessed_docs(self):
        db = self.db
        lst = db(db.TblDocs.crc == None).select(db.TblDocs.id)
        lst = [rec.id for rec in lst]
        for doc_id in lst:
            self.process_ported_doc(doc_id)
    

