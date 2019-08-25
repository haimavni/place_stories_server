import ws_messaging
import datetime

@serve_json
def read_chatroom(vars):
    messages = db(db.TblChats.chat_group==int(vars.room_number)).select()
    for msg in messages:
        msg.sender_name = auth.user_name(msg.author)
        msg.message = msg.message.replace('\n', '<br/>')
    chatroom_name = db(db.TblChatGroup.id==int(vars.room_number)).select().first().name
    return dict(chatroom_name=chatroom_name,
                messages=messages,
                user_message='')

@serve_json
def read_chatrooms(vars):
    lst = db(db.TblChatGroup).select()
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
    db.TblChats.insert(chat_group=chatroom_id,
                       author=user_id,
                       timestamp=now,
                       message=vars.user_message)
    ws_messaging.send_message(key='INCOMING_MESSAGE' + vars.room_number, 
                              group='CHATROOM' + vars.room_number,
                              author=user_id,
                              timestamp=str(now)[:19],
                              sender_name=auth.user_name(user_id),
                              message=vars.user_message.replace('\n', '<br/>'))
    notify_chatters(user_id, chatroom_id)
    return dict(good=True)

@serve_json
def delete_message(vars):
    good = db(db.TblChats.id==vars.message.id).delete() == 1
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

def notify_chatters(user_id, chatroom_id):
    messages = db(db.TblChats.id==chatroom_id).select() #todo: also ignore very recent ones?
    chatroom = db(db.TblChatGroup.id==chatroom_id).select().first()
    now = datetime.datetime.now()
    if chatroom.story_id:
        story = db(db.TblStories.id==chatroom.story_id)
        story.update_record(last_chat_time=now)
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
    New activity in a discussion group
    ''')
    mail.send(to=receivers, subject='New activity in chatroom', app=request.application, message=message)
    #todo: collect relevant chatters. email them that a message was added. include link to the relevant page.