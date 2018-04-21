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
    chatroom_id = db.TblChatGroup.insert(name=vars.new_chatroom_name,
                                         moderator_id=auth.current_user())
    return dict(chatroom_id=chatroom_id)

@serve_json
def send_message(vars):
    now = datetime.datetime.now()
    user_id = auth.current_user() or vars.user_id or 2
    db.TblChats.insert(chat_group=int(vars.room_number),
                       author=user_id,
                       timestamp=now,
                       message=vars.user_message)
    ws_messaging.send_message(key='INCOMING_MESSAGE' + vars.room_number, 
                              group='CHATROOM' + vars.room_number,
                              author=user_id,
                              timestamp=str(now)[:19],
                              sender_name=auth.user_name(user_id),
                              message=vars.user_message.replace('\n', '<br/>'))
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

