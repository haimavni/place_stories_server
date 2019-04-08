from words import calc_used_languages, read_words_index, get_all_story_previews, get_reisha
import stories_manager
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids

@serve_json
def get_term_list(vars):
    lst = db((db.TblStories.used_for == STORY4TERM) & \
             (db.TblStories.deleted != True) & \
             ###(db.TblTerms.deleted != True) & \
             (db.TblTerms.story_id == db.TblStories.id)).select(orderby=db.TblStories.name)
    result = [dict(story_text=rec.TblStories.story,
                   preview=get_reisha(rec.TblStories.preview, 40),
                   name=rec.TblStories.name, 
                   story = get_story_by_id(rec.TblTerms.story_id),
                   story_id=rec.TblStories.id, 
                   source=rec.TblStories.source,
                   id=rec.TblTerms.id) for rec in lst]
    return dict(term_list=result)

@serve_json
def delete_term(vars):
    rec = db(db.TblTerms.id == int(vars.term_id)).select().first()
    rec.update(deleted=True)
    story_id = rec.story_id
    db(db.TblStories.id == story_id).update(deleted=True)
    return dict()

def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)

@serve_json
def apply_to_checked_terms(vars):
    all_tags = calc_all_tags()
    params = vars.params
    sdl = params.checked_term_list
    st = params.selected_topics
    added = []
    deleted = []
    changes = dict()
    for story_id in sdl:
        trec = db(db.TblTerms.story_id==story_id).select().first()
        curr_tag_ids = set(get_tag_ids(trec.id, 'T'))
        for tpc in st:
            topic = tpc.option
            term_id = trec.id
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type='T', item_id=term_id, topic_id=topic.id, story_id=story_id) 
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if 'T' not in topic_rec.usage:
                    usage = topic_rec.usage + 'T'
                    topic_rec.update_record(usage=usage, topic_kind=2) #topic is simple 
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=='T') & (db.TblItemTopics.item_id==term_id) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[term_id] = dict(keywords=keywords, term_id=term_id)
        rec = db(db.TblTerms.id==term_id).select().first()
        rec.update_record(keywords=keywords)  #todo: remove this line soon
        rec = db(db.TblStories.id==rec.story_id).select().first()
        rec.update_record(keywords=keywords)
    return dict()

