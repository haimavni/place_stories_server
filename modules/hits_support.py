import stories_manager
from injections import inject


def add_missing_bios():
    db = inject("db")
    q = db.TblMembers.story_id == None
    for member_rec in db(q).select():
        attach_bio_to_member(member_rec)

        
def add_missing_article_stories():
    db = inject("db")
    q = db.TblArticles.story_id == None
    for article_rec in db(q).select():
        attach_story_to_article(article_rec)

        
def fix_hit_stories():
    handle_itemless_hits()
    add_missing_bios()
    add_missing_article_stories()
    for what in ("EVENT", "TERM"):
        calc_story_id_of_event_or_term(what)
    add_story_ids() #other than EVENT/TERM
        
#---------------internal---------------------------- 


def handle_itemless_hits():
    db = inject("db")
    for hit in db(((db.TblPageHits.item_id == None) | (db.TblPageHits.item_id == 0)) & (db.TblPageHits.what != "APP")).select():
        hit.update_record(what="APP")

        
def new_bio(name):
    STORY4MEMBER = inject("STORY4MEMBER")
    sm = stories_manager.Stories()
    story_info = sm.get_empty_story(used_for=STORY4MEMBER, story_text="", name=name)
    result = sm.add_story(story_info)
    return result.story_id


def attach_bio_to_member(member_rec):
    if member_rec.story_id:
        return
    name = (member_rec.first_name or "") + " " + (member_rec.last_name or "")
    name = name.strip()
    story_id = new_bio(name)
    member_rec.update_record(story_id=story_id)

    
def new_article_story(name):
    STORY4ARTICLE = inject("STORY4ARTICLE")
    sm = stories_manager.Stories()
    story_info = sm.get_empty_story(used_for=STORY4ARTICLE, story_text="", name=name)
    result = sm.add_story(story_info)
    return result.story_id


def attach_story_to_article(article_rec):
    if article_rec.story_id:
        return
    name = article_rec.name.strip()
    story_id = new_article_story(name)
    article_rec.update_record(story_id=story_id)
    

def calc_story_id_of_event_or_term(what):
    db = inject("db")
    hits = db((db.TblPageHits.what == what) & (db.TblPageHits.story_id == None)).select()
    for hit in hits:
        if not hit.item_id:
            hit.update_record(what="APP")
            continue
        story = db(db.TblStories.id == hit.item_id).select(db.TblStories.name, db.TblStories.used_for).first()
        if story:
            true_what = what_of_used_for(story.used_for)
            tbl = table_of_hit_what(true_what)
            story_id = hit.item_id
            item = None
            item_id = 0
            if tbl:
                item = db(tbl.story_id == story_id).select().first()
                if item:
                    item_id = item.id
            hit.update_record(what=true_what, item_id=item_id, story_id=story_id)

                
def add_story_id(what):
    db = inject("db")
    hits = db((db.TblPageHits.what == what) & (db.TblPageHits.story_id == None)).select()
    for hit in hits:
        tbl = table_of_hit_what(what)
        rec = db(tbl.id == hit.item_id).select().first()
        if rec:
            hit.update_record(story_id=rec.story_id)

            
def add_story_ids():
    for what in ("MEMBER", "PHOTO", "VIDEO", "DOC", "ARTICLE", "DOCSEGMENT"):
        add_story_id(what)           
        
    
def what_of_used_for(used_for):
    STORY4MEMBER, STORY4EVENT, STORY4PHOTO, STORY4TERM, STORY4MESSAGE, STORY4VIDEO, STORY4DOC, STORY4ARTICLE, STORY4DOCSEGMENT, STORY4HELP = inject(
        'STORY4MEMBER', 'STORY4EVENT', 'STORY4PHOTO', 'STORY4TERM', 'STORY4MESSAGE', 'STORY4VIDEO', 'STORY4DOC', 'STORY4ARTICLE', 'STORY4DOCSEGMENT', 'STORY4HELP')
    dic = {STORY4MEMBER: "MEMBER",
                STORY4EVENT: "EVENT",
                STORY4PHOTO: "PHOTO",
                STORY4TERM: "TERM",
                STORY4MESSAGE: "MESSAGE",
                STORY4VIDEO: "VIDEO",
                STORY4DOC: "DOC",
                STORY4ARTICLE: "ARTICLE",
                STORY4HELP: "HELP",
                STORY4DOCSEGMENT:"DOCSEGMENT"
    }
    return dic[used_for]

    
def table_of_hit_what(what):
    db = inject("db")
    tables = dict(
        MEMBER=db.TblMembers,
        ARTICLE=db.TblArticles,
        EVENT=db.TblEvents,
        PHOTO=db.TblPhotos,
        TERM=db.TblTerms,
        DOC=db.TblDocs,
        DOCSEG=db.TblDocSegments,
        VIDEO=db.TblVideos,
        HELP=None,
        MESSAGE=None
    )
    return tables[what]    
    
