import random
import time
from date_utils import fix_all_date_ends

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

def _apply_fixes():
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
    db(db.TblConfiguration.id==1).update(fix_level=last_fix + 1000)        
    for f in sorted(_fixes):
        if f > last_applied_fix:
            _fixes[f]()
    db(db.TblConfiguration.id==1).update(fix_level=last_fix)

def init_photo_back_sides():
    db(db.TblPhotos.is_back_side==None).update(is_back_side=False)

_fixes = {
    1: init_photo_back_sides,
    2: fix_all_date_ends
}

_init_configuration_table()
_apply_fixes()

    