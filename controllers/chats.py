import ws_messaging
import datetime
from send_email import email
import re

@serve_json
def read_chatroom(vars):
    messages = db(db.TblChats.chat_group==int(vars.room_number)).select()
    for msg in messages:
        msg.sender_name = auth.user_name(msg.author)
        msg.message = msg.message.replace('\n', '<br/>')
    crec = db(db.TblChatGroup.id==int(vars.room_number)).select().first()
    chatroom_name = crec.name if crec else ""
    return dict(chatroom_name=chatroom_name,
                messages=messages,
                user_message='')

@serve_json
def read_chatrooms(vars):
    lst = db(db.TblChatGroup.story_id==None).select() #chats with story id belong to specific objects
    for rec in lst:
        rec.user_message = 'bla'
    dic = dict()
    for i, rec in enumerate(lst):
        dic[rec.id] = i
    return dict(chatrooms=lst, chatroom_index=dic)

@serve_json
def add_chatroom(vars):
    story_id = int(vars.story_id) if vars.story_id else None
    chatroom_id = None
    if story_id:
        chatroom = db(db.TblChatGroup.story_id==story_id).select().first()
        chatroom_id = chatroom.id if chatroom else None
    if not chatroom_id:
        chatroom_id = db.TblChatGroup.insert(name=vars.new_chatroom_name,
                                            moderator_id=auth.current_user(),
                                            story_id=story_id)
    if story_id:
        db(db.TblStories.id==story_id).update(chatroom_id=chatroom_id)
    return dict(chatroom_id=chatroom_id)

@serve_json
def send_message(vars):
    chatroom_id = int(vars.room_number)
    now = datetime.datetime.now()
    user_id = auth.current_user() or int(vars.user_id) if vars.user_id else 2
    message = message_to_link(vars.user_message)
    db.TblChats.insert(chat_group=chatroom_id,
                       author=user_id,
                       timestamp=now,
                       message=message)
    ws_messaging.send_message(key='INCOMING_MESSAGE' + str(vars.room_number),
                              group='CHATROOM' + str(vars.room_number),
                              author=user_id,
                              timestamp=str(now)[:19],
                              sender_name=auth.user_name(user_id),
                              message=message.replace('\n', '<br/>'))
    notify_chatters(user_id, chatroom_id)
    return dict(good=True)

@serve_json
def delete_message(vars):
    good = db(db.TblChats.id==vars.message.id).delete()
    return dict(deleted=good)

@serve_json
def update_message(vars):
    now = datetime.datetime.now()
    user_id = auth.current_user() or vars.user_id or 2
    msg_id = vars.msg_id
    db(db.TblChats.id==msg_id).update(
        author=user_id,
        timestamp=now,
        message=vars.user_message
    )
    return dict()

@serve_json
def rename_chatroom(vars):
    chatroom_id = int(vars.room_number)
    chat_rec = db(db.TblChatGroup.id==chatroom_id).select().first()
    chat_rec.update_record(name=vars.new_chatroom_name)         
    return dict()

@serve_json
def delete_chatroom(vars):
    chatroom_id = int(vars.room_number)
    q = db.TblChatGroup.id==chatroom_id
    grec = db(q).select().first()
    grec.update_record(story_id=None) #otherwise the story is deleted due to cascading
    db(q).delete()
    ws_messaging.send_message(key='DELETE_CHATROOM', group='ALL', room_number=chatroom_id);
    return dict()

@serve_json
def disconnect_chatroom(vars):
    chatroom_id = int(vars.room_number)
    n = db(db.TblChats.chat_group==chatroom_id).count()
    if n > 0:
        return dict()
    chat_group = db(db.TblChatGroup.id==chatroom_id).select().first()
    if not chat_group:
        return dict()
    story_id = chat_group.story_id
    if not story_id:
        return dict()
    story_rec = db(db.TblStories.id==story_id).select().first()
    if not story_rec:
        return dict()
    story_rec.update_record(chatroom_id=None)
    return dict(disconnected=True)

@serve_json
def chatroom_deleted(vars):
    story_id = int(vars.story_id)
    srec = db(db.TblStories.id==story_id).select(db.TblStories.id, db.TblStories.chatroom_id).first()
    if srec:
        srec.update_record(chatroom_id=None)
    return dict()

#---------------support functions---------------------

def notify_chatters(user_id, chatroom_id):
    messages = db(db.TblChats.id==chatroom_id).select() #todo: also ignore very recent ones?
    chatroom = db(db.TblChatGroup.id==chatroom_id).select().first()
    now = datetime.datetime.now()
    url = ''
    if chatroom.story_id:
        story = db(db.TblStories.id==chatroom.story_id).select().first()
        story.update_record(last_chat_time=now)
        url = calc_url(story)
        #url by story usage
    hour_ago = now - datetime.timedelta(hours=1)
    msgs = [msg for msg in messages if (msg.timestamp < hour_ago) and (msg.author != user_id)]
    users = [msg.author for msg in msgs]
    if not users:
        return
    users = set(users)
    receivers = db(db.auth_user.id.belongs(users)).select(db.auth_user.email)
    receivers = [r.email for r in receivers]
    message = ('', '''
    New activity in a discussion group of {app}.
    <br>
    Click <a href="{host}{url}">here</a> to view the messages.
    '''.format(host=request.env.http_host.split(':')[0], app=request.application, url=url))
    email(receivers=receivers, subject='New activity in chatroom', message=message)
    #todo: collect relevant chatters. email them that a message was added. include link to the relevant page.
    
def calc_url(story):
    if story.used_for == STORY4EVENT:
        return '/{app}/static/aurelia/index-{app}.html#/story-detail/{sid}/*?search_type=simple&what=story'.format(app=request.application, sid=story.id)
    if story.used_for == STORY4TERM:
        return '/{app}/static/aurelia/index-{app}.html#/term-detail/{sid}/*?what=term'.format(app=request.application, sid=story.id)
    if story.used_for == STORY4PHOTO:
        photo = db(db.TblPhotos.story_id==story.id).select().first()
        pid = photo.id
        if photo:
            return '/{app}/static/aurelia/index.html#/photo-detail/{pid}/*'.format(app=request.application, pid=story.id)
    return ''

def message_to_link(message):
    pat = r"(?P<url>https?:\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]))"
    match = re.search(pat, message)
    comment(f"message is {message}. match is {match}")
    if not match:
        return message
    url = match.group(0)
    msg = message.replace(url, '') or "Click here"
    return f'<a href="{url}">{msg}</a>'
