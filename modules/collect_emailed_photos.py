import email
import base64
import re
import zlib
from os import listdir
from os.path import isfile, join, splitext
from photos import save_uploaded_photo
from gluon.storage import Storage
from email.header import decode_header
from shutil import move
from injections import inject

class EmailPhotosCollector:

    def __init__(self, maildir, output_folder):
        self.output_folder = output_folder
        self.maildir = maildir #'/home/photos/Maildir'
        self.photo_collection = []

    def collect(self):
        maildir_new = self.maildir + '/new'
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
            parts = s.split('<')
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

    def handle_image(self, msg):
        disposition = msg.get('content-disposition')
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

def test_collect_mail():
    email_photos_collector = EmailPhotosCollector(maildir='/home/haim/tmp/maildir', output_folder='/home/haim/tmp/photos/')
    results = []
    for msg in email_photos_collector.collect():
        user_id = get_user_id_of_sender(msg.sender_email, msg.sender_name)
        user_id = user_id or 1 #if we decide not to create new user
        text = msg.html_content or msg.plain_content
        print 'subject: ', msg.subject, ' image names: ', msg.images.keys(), msg.sender_email
        num_duplicates = num_failed = 0
        photo_ids = []
        for image_name in msg.images:
            result = save_uploaded_photo(image_name, msg.images[image_name], user_id)
            if result == 'duplicate':
                num_duplicates += 1
            elif result == 'failed':
                num_failed += 1
            else:
                photo_ids.append(result)
            result = "{} duplicates, {} failed, {} uploaded photos".format(num_duplicates, num_failed, len(photo_ids))
            results.append(result)
    return results

if __name__ == "__main__":
    # execute only if run as a script
    test()  


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def send_mail(subject, frm, to, msg):

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"]    = frm
    message["To"]      = to

    message.attach(MIMEText(msg, "plain"))

    try:
        server = smtplib.SMTP("localhost")
        server.sendmail(
            message["From"],
            message["To"],
             message.as_string()
        )
        server.quit()
    except smtplib.SMTPException:
        print("e-mail send error")        