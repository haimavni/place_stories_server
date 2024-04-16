from port_db import Migrate

#1=scratch, 2=migrate, 3=process photos, 4=process docs: "
what = 4

num_event_stories= db(db.TblStories.used_for==STORY4EVENT).count()
num_events = db(db.TblEvents).count()

migrate = Migrate()
if what == 1:
    x = migrate.start_from_scratch()

#plan = migrate.read_plan()

#_plan_legth = len(plan)
if what == 2:
    result = migrate.execute_plan(first=400, limit=200)


migrate.execute_plan = None

Migrate = None
migrate = None

#--------------------------------------
from process_ported_photos import ProcessPortedPhotos
ppp = ProcessPortedPhotos()
if what == 3:
    photos_result = ppp.process_all_unprocessed_photos()
ProcessPortedPhotos = None
ppp.process_all_unprocessed_photos = None
ppp = None

#---------------------------------------
from process_ported_docs import ProcessPortedDocs
ppd = ProcessPortedDocs()
if what == 4:
    docs_result = ppd.process_unprocessed_docs()
ProcessPortedDocs = None
ppd.process_unprocessed_docs = None
ppd = None

