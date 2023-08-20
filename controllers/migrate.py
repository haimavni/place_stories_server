from port_db import Migrate
from process_ported_photos import ProcessPortedPhotos
from process_ported_docs import ProcessPortedDocs

def start_from_scratch():
    migrate = Migrate()
    migrate.start_from_scratch()
    return "Database reinitialized"

def build_database():
    migrate = Migrate()
    return migrate.execute_plan(first=0, limit=10000)

def process_ported_photos():
    ppp = ProcessPortedPhotos()
    return  ppp.process_all_unprocessed_photos()

def process_ported_docs():
    ppd = ProcessPortedDocs()
    return ppd.process_unprocessed_docs()
