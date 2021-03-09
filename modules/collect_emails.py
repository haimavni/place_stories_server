import email
import base64
import re
import zlib
from os import listdir
from os.path import isfile, join, splitext
from .photos_support import save_uploaded_photo_collection
from gluon.storage import Storage
from email.header import decode_header
from shutil import move
from .injections import inject
from io import StringIO
from mammoth import convert_to_html

class EmailCollector:

    def __init__(self):
        request, comment, logger = inject('request', 'comment', 'logger')
        self.maildir = '/home/{}_mailbox/Maildir'.format(request.application)
        comment('init EmailCollector')
        logger.debug('init EmailCollector')
        

    def collect(self):
        maildir_new = self.maildir + '/new'
        comment = inject('comment')
        comment('maildir new: {}', maildir_new)
        msg_list = [join(maildir_new, f) for f in listdir(maildir_new) if isfile(join(maildir_new, f))]
        for msg_file in msg_list:
            result = self.handle_msg(msg_file)
            yield result

    def handle_msg(self, msg_file):
        from email.parser import Parser
        parser = Parser()
        result = Storage(images=dict())
        with open(msg_file) as fp:
            x = parser.parse(fp)
            items = x.walk()
            for item in items:
                self.handle_message_item(item, result)
        dst = msg_file.replace('/new/', '/cur/')
        move(msg_file, dst)
        return result
    
    def get_header_info(self, msg, result):
        comment = inject('comment')
        if result.sender:
            return #already done though in the wrong place
        result.sender = msg.get('from')
        if not result.sender:
            return
        lst = decode_header(result.sender)
        if len(lst) == 2:
            result.sender_name = lst[0][0]
            result.sender_email = lst[1][0][1:-1] #get rid of <>
        else:
            s = lst[0][0]
            comment("sender email {}", s)
            parts = s.split('<')
            if len(parts) == 1:
                result.sender_email = s
            elif parts:
                result.sender_name = parts[0].strip()
                result.sender_email = parts[1][:-1]
        result.to = msg.get('to')
        result.what = result.to.split('@')[0]
        subject = msg.get('subject')
        lst = decode_header(subject)
        lst = [itm[0] for itm in lst]
        result.subject = ' '.join(lst)
        result.date = msg.get('date')

    def handle_message_item(self, msg, result):
        content_type = msg.get_content_maintype();
        content_subtype = msg.get_content_subtype();
        if content_type == 'image':
            filename, blob = self.handle_image(msg)
            if blob:
            	result.images[filename] = blob
        elif content_type == 'text':
            if content_subtype == 'plain':
                if not result.sender:  #some messages do not behave...
                    self.get_header_info(msg, result)
                result.plain_content = self.handle_text(msg)
            elif content_subtype == 'html':
                result.html_content = self.handle_text(msg)
        elif content_type == 'multipart':
            self.get_header_info(msg, result)
        elif content_type == 'application':
            self.get_application_info(msg, content_subtype, result)
            
    def get_application_info(self, msg, content_subtype, result):
        disposition = msg.get('content-disposition')
        if disposition.endswith('"'):
            disposition = disposition[:-1]
        x = decode_header(disposition)
        blob = msg.get_payload(decode=True)
        if content_subtype == 'vnd.openxmlformats-officedocument.wordprocessingml.document':
            self.handle_docx(blob, result)
    
    def handle_docx(self, blob, result):
        stream = StringIO(blob)
        temp = convert_to_html(stream)
        result.html_content = temp.value # The generated HTML
        messages = temp.messages # Any messages, such as warnings during conversion

    def handle_image(self, msg):
        disposition = msg.get('content-disposition')
        if not disposition:
	        return None,None
        if disposition.endswith('"'):
            disposition = disposition[:-1]
        x = decode_header(disposition)
        if len(x) > 1:
            filename = x[1][0]
        else:
            m = re.search(r'"(.+)', disposition)
            if m:
                filename = m.group(1)
                if filename.endswith('"'):
                    filename = filename[:-1]
            else:
                filename = "Unknown"
        blob = msg.get_payload(decode=True)
        return filename, blob

    def handle_text(self, msg):
        return msg.get_payload(decode=True)

def get_user_id_of_sender(sender_email, sender_name):
    auth = inject('auth')
    return auth.user_id_of_email(sender_email)

def collect_mail():
    try:
        db, comment, logger, mail, MAIL_WATCHER, log_exception = inject('db', 'comment', 'logger', 'mail', 'MAIL_WATCHER', 'log_exception')
        email_photos_collector = EmailCollector()
        results = []
        lst = db((db.auth_membership.group_id==MAIL_WATCHER)&(db.auth_user.id==db.auth_membership.user_id)&(db.auth_user.id>1)).select(db.auth_user.email)
        receivers = [r.email for r in lst]    
        logger.debug('collecting mail')
        for msg in email_photos_collector.collect():
            user_id = get_user_id_of_sender(msg.sender_email, msg.sender_name)
            if not user_id:
                emsg = 'mail sent by {} {}'.format(msg.sender_email, msg.sender_name)
                mail.send(sender="admin@gbstories.org", to=receivers, subject="incoming email to gbstories from unknown sender", message=emsg)
                continue
            ###user_id = user_id or 1 #todo: if we decide not to create new user
            text = msg.html_content or msg.plain_content
            comment('New email: subject: {subject}, images: {image_names} sent by {sender}', 
                    subject=msg.subject, image_names=list(msg.images.keys()), sender=msg.sender_email)
            if msg.images:
                result = save_uploaded_photo_collection(msg.images, user_id)
                results.append(result)
                comment("upload result {result}", result=result)
            emsg = ''
            for fld in sorted(msg):
                if fld == "images":
                    emsg += '{} images\n'.format(len(msg.images))
                else:
                    s = "strange text"
                    m = msg[fld]
                    s = m
                    emsg += fld + ': ' + s + '\n'
            result = mail.send(sender="admin@gbstories.org", to=receivers, subject="incoming email to gbstories", message=emsg)
            if result:
                comment("mail was forwarded")
            else:
                comment("forwarding mail failed: {}", mail.error)
    except Exception as e:
        log_exception('Error collecting mail')
        raise
            
        
    return results
