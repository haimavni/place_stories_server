from audios_support import save_uploaded_audio, audio_url
from members_support import calc_grouped_selected_options, calc_all_tags, get_tag_ids, init_query, get_topics_query
from gluon.storage import Storage
from date_utils import date_of_date_str, parse_date, get_all_dates, update_record_dates, fix_record_dates_in, fix_record_dates_out
import stories_manager

@serve_json
def get_audio_list(vars):
    params = vars.params
    if params.checked_audio_list:
        q = (db.TblAudios.story_id.belongs(params.checked_audio_list)) & (db.TblStories.id==db.TblAudios.story_id)
        lst0 = db.select(q)
        lst0 = [rec for rec in lst0]
        for rec in lst0:
            rec.TblAudios.checked = True
    else:
        lst0 = []
    q = make_audios_query(params)
    lst = db(q).select(orderby=~db.TblAudios.id)
    lst = [rec.TblAudios for rec in lst if rec.TblAudios.story_id not in params.checked_audio_list]
    lst = lst0 + lst
    audio_list = []
    for rec1 in lst:
        rec = rec1.TblAudios
        fix_record_dates_out(rec)
        story = get_story_by_id(rec.story_id)
        rec.story = story
        rec.audio_path = audio_url(rec.story_id)
        rec.keywords = rec1.keywords
        audio_list.append(rec)
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
        curr_tag_ids = set(get_tag_ids(story_id, 'A'))
        audio_id = drec.id
        for tpc in st:
            topic = tpc.option
            if topic.sign=="plus" and topic.id not in curr_tag_ids:
                new_id = db.TblItemTopics.insert(item_type='A', topic_id=topic.id, story_id=story_id)
                curr_tag_ids |= set([topic.id])
                ###added.append(item)
                topic_rec = db(db.TblTopics.id==topic.id).select().first()
                if topic_rec.topic_kind == 0: #never used
                    new_topic_was_added = True
                if 'A' not in topic_rec.usage:
                    usage = topic_rec.usage + 'A'
                    topic_rec.update_record(usage=usage, topic_kind=2) #topic is simple 
            elif topic.sign=="minus" and topic.id in curr_tag_ids:
                q = (db.TblItemTopics.item_type=='A') & (db.TblItemTopics.story_id==story_id) & (db.TblItemTopics.topic_id==topic.id)
                curr_tag_ids -= set([topic.id])
                ###deleted.append(item)
                db(q).delete()
        if recorder_id:
            drec.update_record(recorder_id=recorder_id)
            
        curr_tags = [all_tags[tag_id] for tag_id in curr_tag_ids]
        keywords = "; ".join(curr_tags)
        changes[audio_id] = dict(keywords=keywords, audio_id=audio_id)
        db(db.TblStories.id==story_id).update(keywords=keywords, is_tagged=bool(keywords))
        if dates_info:
            update_record_dates(rec, dates_info)
    ###changes = [changes[audio_id] for audio_id in adl]
    ###ws_messaging.send_message('AUDIO-TAGS-CHANGED', group='ALL', changes=changes)
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
    if params.selected_topics:
        q1 = get_topics_query(params.selected_topics)
        q &= q1
    return q

def get_story_by_id(story_id):
    sm = stories_manager.Stories()
    return sm.get_story(story_id)


