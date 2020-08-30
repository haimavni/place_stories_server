from audios_support import save_uploaded_audio, audio_url
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids, init_query
from gluon.storage import Storage
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
import stories_manager

@serve_json
def get_audio_list(vars):
    params = vars.params
    if params.checked_audio_list:
        lst0 = db(db.TblAudios.story_id.belongs(params.checked_audio_list)).select()
        lst0 = [rec for rec in lst0]
        for rec in lst0:
            rec.checked = True
    else:
        lst0 = []
    selected_topics = params.selected_topics or []
    if selected_topics:
        lst = get_audio_list_with_topics(params)
    else:
        q = make_audios_query(params)
        lst = db(q).select(orderby=~db.TblAudios.id)
    selected_audio_list = params.selected_audio_list
    lst = [rec for rec in lst if rec.story_id not in params.checked_audio_list]
    lst = lst0 + lst
    audio_list = [rec for rec in lst]
    for rec in audio_list:
        fix_record_dates_out(rec)
        story = get_story_by_id(rec.story_id)
        rec.story = story
        rec.audio_path = audio_url(rec.story_id)
    return dict(audio_list=audio_list, no_results=not audio_list)

@serve_json
def upload_audio(vars):
    comment("start handling uploaded audio file")
    user_id = int(vars.user_id) if vars.user_id else auth.current_user()
    fil = vars.file
    result = save_uploaded_audio(fil.name, fil.BINvalue, user_id)
    return dict(upload_result=result)

@serve_json
def apply_to_checked_audios(vars):
    all_tags = calc_all_tags()
    params = vars.params
    adl = params.checked_audio_list
    if params.audios_date_str:
        dates_info = dict(
            audio_date = (params.audios_date_str, params.audios_date_span_size)
        )
    else:
        dates_info = None

    st = params.selected_topics
    rlist = params.selected_recorders
    if len(rlist) == 1:
        recorder_id = rlist[0].option.id
    else:
        recorder_id = None
    added = []
    deleted = []
    changes = dict()
    new_topic_was_added = False
    for story_id in adl:
        drec = db(db.TblAudios.story_id==story_id).select().first()
        curr_tag_ids = set(get_tag_ids(drec.id, 'A'))
        audio_id = drec.id
        for tpc in st:
            topic = tpc.option
            ###item = dict(item_id=audio_id, topic_id=topic.id)
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type='A', item_id=audio_id, topic_id=topic.id, story_id=story_id) 
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if topic_rec.topic_kind == 0: #never used
                    new_topic_was_added = True
                if 'A' not in topic_rec.usage:
                    usage = topic_rec.usage + 'A'
                    topic_rec.update_record(usage=usage, topic_kind=2) #topic is simple 
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=='A') & (db.TblItemTopics.item_id==audio_id) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                db(q).delete()
        if recorder_id:
            drec.update_record(recorder_id=recorder_id)
            
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[audio_id] = dict(keywords=keywords, audio_id=audio_id)
        rec = db(db.TblAudios.id==audio_id).select().first()
        rec.update_record(keywords=keywords)  #todo: remove this line soon
        rec = db(db.TblStories.id==rec.story_id).select().first()
        rec.update_record(keywords=keywords, is_tagged=bool(keywords))
        if dates_info:
            update_record_dates(rec, dates_info)
    ###changes = [changes[audio_id] for audio_id in adl]
    ###ws_messaging.send_message('audio-TAGS-CHANGED', group='ALL', changes=changes)
    return dict(new_topic_was_added=new_topic_was_added)

@serve_json
def add_recorder(vars):
    recorder_name = vars.recorder_name
    if not db(db.TblRecorders.name == recorder_name).isempty():
        raise User_Error("!audios.recorder-already-exists")
    db.TblRecorders.insert(name=recorder_name)
    ws_messaging.send_message(key='RECORDER_ADDED', group='ALL', recorder_name=recorder_name)
    return dict()

@serve_json
def get_recorder_list(vars):
    recorder_list = db(db.TblRecorders).select()
    return dict(recorder_list = recorder_list)

#----------------support functions-----------------

def get_audio_list_with_topics(vars):
    first = True
    topic_groups = calc_grouped_selected_options(vars.selected_topics)
    for topic_group in topic_groups:
        q = make_audios_query(vars) #if we do not regenerate it the query becomes accumulated and necessarily fails
        q &= (db.TblItemTopics.item_id==db.TblAudios.id) & (db.TblItemTopics.item_type.like('%A%'))
        ##topic_ids = [t.id for t in topic_group]
        sign = topic_group[0]
        topic_group = topic_group[1:]
        q1 = db.TblItemTopics.topic_id.belongs(topic_group)
        if sign == 'minus':
            q1 = ~q1
        q &= q1
        lst = db(q).select(orderby=~db.TblAudios.id)
        lst = [rec.TblAudios for rec in lst]
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

def make_audios_query(params):
    q = init_query(db.TblAudios, editing=params.editing)
    if params.days_since_upload:
        days = params.days_since_upload.value
        if days:
            upload_date = datetime.datetime.today() - datetime.timedelta(days=days)
            q &= (db.TblAudios.upload_date >= upload_date)
    if params.selected_recorders:
        selected_recorders = [r.option.id for r in params.selected_recorders]
        q &= (db.TblAudios.recorder_id.belongs(selected_recorders))
    opt = params.selected_uploader
    if opt == 'mine':
        q &= (db.TblAudios.uploader==params.user_id)
    elif opt == 'users':
        q &= (db.TblAudios.uploader!=None)
    opt = params.selected_dates_option
    if opt == 'selected_dates_option':
        pass
    elif opt == 'dated':
        q &= (db.TblAudios.audio_date != NO_DATE)
    elif opt == 'undated':
        q &= (db.TblAudios.audio_date == NO_DATE)
    if params.selected_audios:
        q &= (db.TblAudios.story_id.belongs(params.selected_audios))
    return q

def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)


