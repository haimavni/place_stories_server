from photos_support import save_article_face
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
from folders import photos_folder
import ws_messaging

@serve_json
def article_list(vars):
    q = (db.TblArticles.deleted != True)
    lst = db(q).select()
    arr = [Storage(id=rec.id,
                   name=rec.name,
                   date_start=rec.date_start,
                   date_end=rec.date_end,
                   has_profile_photo=bool(rec.facePhotoURL), #used in client!
                   rnd=random.randint(0, 1000000),
                   facePhotoURL=photos_folder('profile_photos') + (rec.facePhotoURL or "dummy_face.png")) for rec in lst]
    arr.sort(key=lambda item: item.rnd)
    return dict(article_list=arr)

@serve_json
def remove_article(vars):
    article_id = int(vars.article_id)
    deleted = db(db.TblArticles.id == article_id).update(deleted=True) == 1
    if deleted:
        ws_messaging.send_message(key='ARTICLE_DELETED', group='ALL', article_id=article_id)
    return dict(deleted=deleted)

@serve_json
def article_by_name(vars):
    name = vars.name
    q = (db.TblArticles.deleted != True) & (db.TblArticles.name == name)
    articles = db(q).select(db.TblArticles.id)
    article_ids = [rec.id for rec in articles]
    return dict(article_ids=article_ids)

@serve_json
def create_new_article(vars):
    #todo: move code of photos/save_face to module and use it to complete the operation. in the client, go to the new article to edit its data
    name = vars.name
    rec = new_article_rec(name=name)
    rec.article_info.updater_id = auth.current_user()
    rec.article_info.update_time = datetime.datetime.now()
    rec.article_info.date_end = NO_DATE
    rec.article_info.date_start = NO_DATE
    article_id = db.TblArticles.insert(**rec.article_info)
    rec.article_info.id = article_id
    params = Storage(
        face=Storage(x=int(vars.face_x),
                     y=int(vars.face_y),
                     r=int(vars.face_r),
                     photo_id=int(vars.photo_id),
                     article_id=article_id),
        make_profile_photo=True
    )
    tmp = save_article_face(params)
    rec.article_info.face_photo_url = tmp.face_photo_url
    article_rec = get_article_rec(article_id)
    article_rec.facePhotoURL = tmp.face_photo_url
    article_rec = json_to_storage(article_rec)
    ws_messaging.send_message(key='ARTICLE_LISTS_CHANGED', group='ALL', article_rec=article_rec, new_article=True)
    return dict(article_id=article_id, article=rec)

###---------------------support functions

def new_article_rec(name=None):
    new_article = Storage(
        article_info=Storage(
            name=name,
            date_start_dateunit='N',
            date_start=Storage(
                date='',
                span=0
                ),
            date_end_dateunit='N',
            date_end=Storage(
                date='',
                span=0
                ),
            ),
        story_info = Storage(display_version='New Story', story_versions=[], story_text='', story_id=None),
        slides=[],
        article_stories = [],
        facePhotoURL = 'dummy_face.png',
        name=name
    )
    return new_article

def get_article_rec(article_id, prepend_path=False):
    if not article_id:
        return None
    rec = db(db.TblArticles.id==article_id).select().first()
    if not rec:
        return None
    if rec.deleted:
        return None
    if rec.updater_id:
        rec.updater_name = auth.user_name(rec.updater_id)
    dates = get_all_dates(rec)
    rec = Storage(rec.as_dict())
    for d in dates:
        rec[d] = dates[d]
    if prepend_path :
        rec.facePhotoURL = photos_folder('profile_photos') + (rec.facePhotoURL or 'dummy_face.png')
    return rec

