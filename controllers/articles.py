import stories_manager
from photos_support import save_article_face, get_slides_from_photo_list, timestamped_photo_path
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
from folders import photos_folder
import ws_messaging
from words import get_reisha
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS

@serve_json
def article_list(vars):
    q = (db.TblArticles.deleted != True)
    lst = db(q).select()
    arr = [Storage(id=rec.id,
                   name=rec.name,
                   date_start=rec.date_start,
                   date_end=rec.date_end,
                   has_profile_photo=bool(rec.facephotourl), #used in client!
                   rnd=random.randint(0, 1000000),
                   facephotourl=face_photo_url(rec, vars.webpSupported)) for rec in lst]
    arr.sort(key=lambda item: item.rnd)
    return dict(article_list=arr)

def face_photo_url(article_rec, webp_supported):
    folder = photos_folder(PROFILE_PHOTOS)
    if webp_supported:
        path = article_rec.facephotourl_webp or article_rec.facephotourl
    else:
        path = article_rec.facephotourl
    path = path or 'dummy_face.png'
    return folder + path

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
    article_rec.facephotourl = tmp.face_photo_url
    article_rec = json_to_storage(article_rec)
    ws_messaging.send_message(key='ARTICLE_LISTS_CHANGED', group='ALL', article_rec=article_rec, new_article=True)
    return dict(article_id=article_id, article=rec)

@serve_json
def get_article_photo_list(vars):
    if vars.article_id == "new":
        return dict(photo_list=[])
    article_id = int(vars.article_id)
    if vars.what == 'story':
        rec = db(db.TblArticles.story_id == article_id).select().first()
        if rec:
            article_id = rec.id
        else:
            return []
    slides = get_article_slides(article_id)
    return dict(photo_list=slides)

@serve_json
def get_article_details(vars):
    if not vars.article_id:
        raise User_Error(T('article does not exist yet!'))
    if vars.article_id == "new":
        rec = new_article_rec()
        rec.article_info.name="articles.new-article"
        return rec
    art_id = int(vars.article_id)
    if vars.what == 'story': #access article via its life story id
        rec = db(db.TblArticles.story_id == art_id).select().first()
        if rec:
            art_id = rec.id
        else:
            raise Exception('No article for this story {mid}', art_id)
    if vars.shift == 'next':
        art_id += 1
    elif vars.shift == 'prev':
        art_id -= 1
    article_stories = get_article_stories(art_id) + get_article_terms(art_id)
    article_info = get_article_rec(art_id)
    if not article_info:
        raise User_Error('No article there')
    sm = stories_manager.Stories()
    story_info = sm.get_story(article_info.story_id) or Storage(display_version='New Story', topic="article.life-summary", story_versions=[], story_text='', story_id=None)
    story_info.used_for = STORY4ARTICLE
    slides = get_article_slides(art_id)
    article_stories = [story_info] + article_stories;
    return dict(article_info=article_info, 
                story_info=story_info, 
                slides=slides, #todo: duplicate?
                article_stories=article_stories,
                facephotourl = photos_folder(PROFILE_PHOTOS) + (article_info.facephotourl or "dummy_face.png")
                )

@serve_json
def set_article_story_id(vars):
    db(db.TblArticles.id == vars.article_id).update(story_id=vars.story_id)
    sm = stories_manager.Stories()
    sm.set_used_for(vars.story_id, STORY4ARTICLE)
    return dict()

@serve_json
def save_group_articles(vars):
    return save_story_articles(vars.caller_id, vars.caller_type, vars.article_ids)

@serve_json
def add_story_article(vars):
    article_id = vars.candidate_id
    story_id = vars.story_id
    story = db(db.TblStories.id==story_id).select().first()
    if story.used_for == STORY4EVENT:
        event = db(db.TblEvents.story_id == story_id).select().first()
        db.TblEventArticles.insert(article_id=article_id, event_id=event.id)
    elif story.used_for == STORY4TERM:
        term = db(db.TblTerms.story_id == story_id).select().first()
        db.TblTermArticles.insert(article_id=article_id, term_id=term.id)
    else:
        raise Exception("Incompatible story usage")
    return dict()

@serve_json
def save_article_info(vars):
    user_id = vars.user_id
    article_info = vars.article_info
    if 'facephotourl' in article_info:
        del article_info.facephotourl #it is saved separately, not updated in client and can only destroy here
    if article_info:
        tbl = db.TblArticles
        for fld in tbl:
            if fld.type == 'date':
                fld_name = fld.name
                if fld_name + '_dateunit' not in article_info:
                    continue
                unit, date = parse_date(article_info[fld_name].date)
                article_info[fld_name] = date
                article_info[fld_name + '_dateunit'] = unit

        ##--------------handle dates - end--------------------------
        article_info.update_time = datetime.datetime.now()
        article_info.updater_id = vars.user_id or auth.current_user() or 2
        ###article_info.approved = auth.has_articleship(DATA_AUDITOR, user_id=vars.user_id)
        arec = db(db.TblArticles.id==article_info.id).select().first()
        arec.update_record(**article_info)
        #article_rec = json_to_storage(arec)
        #ws_messaging.send_message(key='ARTICLE_LISTS_CHANGED', group='ALL', article_rec=article_rec, new_article=new_article)
    result = Storage(info=article_info)
    #todo: read-modify-write below?
    ##get_article_names() #todo: needed if we use caching again
    
    return dict()

@serve_json
def get_story(vars):
    sm = stories_manager.Stories()
    story_id = int(vars.story_id)
    return dict(story=sm.get_story(story_id))

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
        facephotourl = 'dummy_face.png',
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
        rec.facephotourl = photos_folder(PROFILE_PHOTOS) + (rec.facephotourl or 'dummy_face.png')
    return rec

def get_article_slides(article_id):
    q = (db.TblArticlePhotos.article_id == article_id) & \
        (db.TblPhotos.id == db.TblArticlePhotos.photo_id) & \
        (db.TblPhotos.deleted != True) &\
        (db.TblPhotos.is_back_side != True) &\
        (db.TblStories.id == db.TblPhotos.story_id)
    return get_slides_from_photo_list(q)

def get_article_stories(article_id):
    q = (db.TblEventArticles.article_id == article_id) & \
        (db.TblEventArticles.event_id == db.TblEvents.id) & \
        (db.TblEvents.story_id == db.TblStories.id) & \
        (db.TblStories.deleted == False)
    result = []
    lst = db(q).select()
    for rec in lst:
        event = rec.TblEvents
        story = rec.TblStories
        dic = dict(
            topic = event.name,
            name = story.name,
            story_id = story.id,
            story_text = story.story,
            preview=get_reisha(story.preview),
            source = event.ssource,
            used_for=story.used_for, 
            author_id=story.author_id,
            creation_date=story.creation_date,
            last_update_date=story.last_update_date
        )
        result.append(dic)
    return result

def get_article_terms(article_id):
    return [] #not ready yet

def save_story_articles(caller_id, caller_type, article_ids):
    if caller_type == "story":
        tbl = db.TblEvents
        tbl1 = db.TblEventArticles
        item_fld = tbl1.event_id
    elif caller_type == "term":
        tbl = db.TblTerms
        tbl1 = db.TblTermArticles
        item_fld = db.TblTermArticles.term_id
    else:
        return dict()
    item = db(tbl.story_id == caller_id).select().first()
    qm = (item_fld == item.id) & (db.TblArticles.id == tbl1.article_id)
    old_articles = db(qm).select(db.TblArticles.id)
    old_articles = [m.id for m in old_articles]
    for a in old_articles:
        if a not in article_ids:
            db((tbl1.article_id == a) & (item_fld == item.id)).delete()
    for a in article_ids:
        if a not in old_articles:
            if caller_type == "story":
                tbl1.insert(article_id=a, event_id=item.id)
            else:
                tbl1.insert(article_id=a, term_id=item.id)
    articles = db(db.TblArticles.id.belongs(article_ids)).select()
    return dict(articles=articles)

