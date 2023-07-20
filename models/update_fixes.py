import random
import time
from date_utils import fix_all_date_ends, init_story_dates
from video_support import upgrade_youtube_info
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
            comment(f"applying fix {f}")
            try:
                result = _fixes[f]()
            except Exception as e:
                log_exception('Error applying fixes')
                break
            else:
                if result != "to-be-continued":
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
    
def fix_visibility():
    db(db.TblStories.deleted!=True).update(visibility=SV_PUBLIC)
    
def fix_deleted_forever():
    db(db.TblStories).update(dead=False)
    
def fix_photo_recognized():
    db(db.TblPhotos.Recognized==None).update(Recognized=True)

def fix_pdf_texts():
    db(db.TblDocs.text_extracted==None).update(text_extracted=False)
    db.commit()

def fix_no_slide_show():
    for prec in db(db.TblPhotos.no_slide_show==None).select():
        prec.update_record(no_slide_show=False)
    db.commit()

def fix_youtube_info():
    result = upgrade_youtube_info(chunk=10)
    db.commit()
    if result.total > 0:
        return "to-be-continued" # to avoid timeout it has to be repeated
    else:
        return "done"

def fix_feedback_messages():
    lst = db(db.TblFeedback.fb_message==None).select()
    for fb in lst:
        bf = fb.fb_bad_message
        gf = fb.fb_good_message
        fb.update_record(fb_message = bf + "<br>---------<br>" + gf)
    return "done"

def fix_member_names():
    for mrec in db(db.TblMembers.deleted!=True).select():
        mrec.update_record(name=(mrec.first_name + ' ' if mrec.first_name else "") + (mrec.last_name if mrec.last_name else ""))
    return "done"

def fix_family_connection_stored():
    for mrec in db((db.TblMembers.deleted!=True) & (db.TblMembers.family_connections_stored==None)).select():
        mrec.update_record(family_connections_stored=False)
    return 'done'

_fixes = {
    1: init_photo_back_sides,
    2: fix_all_date_ends,
    3: init_story_dates,
    4: init_sampling,
    5: fix_is_tagged,
    6: fix_visibility,
    7: fix_deleted_forever,
    8: fix_photo_recognized,
    9: fix_pdf_texts,
    10: fix_no_slide_show,
    11: fix_youtube_info,
    12: fix_feedback_messages,
    13: fix_member_names,
    14: fix_family_connection_stored
}

_init_configuration_table()
# _apply_fixes()

    