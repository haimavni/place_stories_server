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
        try:
            with open(fname, 'rb') as f:
                blob = f.read()
        except Exception as e:
            self.log_it(f"file {fname} was not found!")
            return
        crc = zlib.crc32(blob)
        doc_rec.update_record(
            crc=crc
        )
        pdf_jpg_file_name = local_docs_folder() + 'pdf_jpgs/' + doc_rec.doc_path
        pdf_jpg_file_name = pdf_jpg_file_name.replace(".pdf", ".jpg")
        pdf_jpg_folder, fn = os.path.split(pdf_jpg_file_name)
        dir_util.mkpath(pdf_jpg_folder)
        save_pdf_jpg(fname, pdf_jpg_file_name)
        db.commit()
        return doc_id
    
    def process_unprocessed_docs(self):
        db = self.db
        lst = db(db.TblDocs.crc == None).select(db.TblDocs.id)
        lst = [rec.id for rec in lst]
        for doc_id in lst:
            self.process_ported_doc(doc_id)
        remaining = db(db.TblDocs.crc == None).count()
        db.commit()
        return f"{remaining} documents still unprocessed"
    

