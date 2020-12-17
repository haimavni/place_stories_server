import stories_manager
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids, init_query, get_topics_query
from misc_utils import multisort
@serve_json
def apply_to_checked_terms(vars):
    all_tags = calc_all_tags()
    params = vars.params
    sdl = params.checked_term_list
    st = params.selected_topics
    added = []
    deleted = []
    new_topic_was_added = False;
    for story_id in sdl:
        trec = db(db.TblTerms.story_id==story_id).select().first() #get rid of _item_id_
        curr_tag_ids = set(get_tag_ids(story_id, 'T'))
        for tpc in st:
            topic = tpc.option
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type='T', topic_id=topic.id, story_id=story_id)
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if topic_rec.topic_kind == 0: #never used
                    new_topic_was_added = True;
                if 'T' not in topic_rec.usage:
                    usage = topic_rec.usage + 'T'
                    topic_rec.update_record(usage=usage, topic_kind=2) #topic is simple 
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=='T') & (db.TblItemTopics.story_id==story_id) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                db(q).delete()
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        rec = db(db.TblStories.id==trec.story_id).select().first()
        rec.update_record(keywords=keywords, is_tagged=bool(keywords))
    return dict(new_topic_was_added=new_topic_was_added)

@serve_json
def get_term_list(vars):
    params = vars.params
    if params.checked_term_list:
        q = (db.TblTerms.story_id.belongs(params.checked_term_list)) & (db.TblStories.id==db.TblTerms.story_id)
        lst0 = db(q).select()
        lst0 = [rec for rec in lst0]
        for rec in lst0:
            rec.TblTerms.checked = True
    else:
        lst0 = []
    q = make_terms_query(params)
    lst = db(q).select(orderby=~db.TblTerms.id)
    lst = [r for r in lst]
    lst = [rec for rec in lst if rec.TblTerms.story_id not in params.checked_term_list]
    lst = sorted(lst, key=lambda term: term.TblTerms.Name)
    lst = lst0 + lst
    term_list = []
    for rec1 in lst:
        rec = rec1.TblTerms
        story = get_story_by_id(rec.story_id)
        rec.story = story
        rec.keywords = rec1.TblStories.keywords
        term_list.append(rec)
    return dict(term_list=term_list, no_results=not term_list)

#----------------support functions-----------------

def make_terms_query(params):
    q = init_query(db.TblTerms)
    if params.selected_terms:
        q &= (db.TblTerms.story_id.belongs(params.selected_terms))
    if params.selected_topics:
        q1 = get_topics_query(params.selected_topics)
        q &= q1
    return q

def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)

@serve_json
def delete_checked_terms(vars):
    checked_term_list = vars.params.checked_term_list
    db(db.TblTerms.story_id.belongs(checked_term_list)).update(deleted=True)
    db(db.TblStories.id.belongs(checked_term_list)).update(deleted=True)
    return dict()

