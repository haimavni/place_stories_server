import random
import time
from date_utils import fix_all_date_ends, init_story_dates
#from topics_support import fix_is_tagged

def _delay():
    n = random.randint(0, 1000000)
    delay = 1.0 * n / 100000
    time.sleep(delay) #prevent more than one process to create the table

def _init_configuration_table():
    if db(db.TblConfiguration).isempty():
        _delay()
        if db(db.TblConfiguration).isempty():
            db.TblConfiguration.insert()
            db.commit()
            
def __apply_fixes():
    if db(db.TblConfiguration).isempty():
        return
    last_fix = sorted(_fixes)[-1]
    last_applied_fix = db(db.TblConfiguration.id==1).select().first().fix_level or 0
    if last_applied_fix >= last_fix:
        return
    _delay()
    last_applied_fix = db(db.TblConfiguration.id==1).select().first().fix_level or 0
    if last_applied_fix >= last_fix:
        return
    for f in sorted(_fixes):
        if f > last_applied_fix:
            comment("applying fix {}", f)
            try:
                _fixes[f]()
            except Exception, e:
                log_exception('Error applying fixes')
                break
            else:
                db(db.TblConfiguration.id==1).update(fix_level=f)
                db.commit()
    
def _apply_fixes():    
    lock_file_name = '{p}apply-fixes[{a}].lock'.format(p=log_path(), a=request.application)
    if os.path.isfile(lock_file_name):
        return
    with open(lock_file_name, 'w') as f:
        f.write('locked')
    try:
        __apply_fixes()
    finally:  
        if os.path.isfile(lock_file_name):
            os.remove(lock_file_name)

def init_photo_back_sides():
    db(db.TblPhotos.is_back_side==None).update(is_back_side=False)

def init_sampling():
    for story_rec in db((db.TblStories.deleted!= True) & (db.TblStories.sampling_id==None)).select():
        story_rec.update_record(sampling_id=random.randint(1, SAMPLING_SIZE))
    db.commit()
    
def fix_is_tagged():
    schedule_background_task("fix is tagged", "fix_is_tagged")

_fixes = {
    1: init_photo_back_sides,
    2: fix_all_date_ends,
    3: init_story_dates,
    4: init_sampling,
    5: fix_is_tagged
}

_init_configuration_table()
_apply_fixes()

    