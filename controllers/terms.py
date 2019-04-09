from words import calc_used_languages, read_words_index, get_all_story_previews, get_reisha
import stories_manager
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids

@serve_json
def delete_term(vars):
    rec = db(db.TblTerms.id == int(vars.term_id)).select().first()
    rec.update(deleted=True)
    story_id = rec.story_id
    db(db.TblStories.id == story_id).update(deleted=True)
    return dict()

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

@serve_json
def get_term_list(vars):
    params = vars.params
    if params.checked_term_list:
        lst0 = db(db.TblTerms.story_id.belongs(params.checked_term_list)).select()
        lst0 = [rec for rec in lst0]
        for rec in lst0:
            rec.checked = True
    else:
        lst0 = []
    selected_topics = params.selected_topics or []
    if selected_topics:
        lst = get_term_list_with_topics(params)
    else:
        q = make_terms_query(params)
        lst = db(q).select(orderby=~db.TblTerms.id)
    selected_term_list = params.selected_term_list
    lst = [rec for rec in lst if rec.story_id not in params.checked_term_list]
    lst = sorted(lst, cmp=lambda itm1, itm2: -1 if itm1.Name < itm2.Name else +1 if itm1.Name > itm2.Name else 0)
    lst = lst0 + lst
    term_list = [rec for rec in lst]
    for rec in term_list:
        story = get_story_by_id(rec.story_id)
        rec.story = story
    return dict(term_list=term_list, no_results=not term_list)

#----------------support functions-----------------

def get_term_list_with_topics(vars):
    first = True
    topic_groups = calc_grouped_selected_options(vars.selected_topics)
    for topic_group in topic_groups:
        q = make_terms_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblTerms.id) & (db.TblItemTopics.item_type.like('%T%'))
        ##topic_ids = [t.id for t in topic_group]
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
        lst = db(q).select(orderby=~db.TblTerms.id)
        lst = [rec.TblTerms for rec in lst]
        bag1 = set(r.id for r in lst)
        if first:
            first = False
            bag = bag1
        else:
            bag &= bag1
    dic = {}
    for r in lst:
        dic[r.id] = r
    result = [dic[id] for id in bag]
    return result

def make_terms_query(params):
    q = (db.TblTerms.deleted!=True)
    if params.selected_terms:
        q &= (db.TblTerms.story_id.belongs(params.selected_terms))
    return q

def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)

