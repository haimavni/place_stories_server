import email
import base64
import re
import zlib
from os import listdir
from os.path import isfile, join, splitext
from photos import save_uploaded_photo
from gluon.storage import Storage
from email.header import decode_header

class EmailPhotosCollector:
    
    def __init__(self, maildir, output_folder):
        self.output_folder = output_folder
        self.maildir = maildir #'/home/photos/Maildir'
        self.photo_collection = []
        
    def collect(self):
        msg_list = [join(self.maildir, f) for f in listdir(self.maildir) if isfile(join(self.maildir, f))]
        for msg_file in msg_list:
            result = self.handle_msg(msg_file)
            print 'image names: ', result.images.keys()
            
    def handle_message_item(self, msg, result):
        content_type = msg.get_content_maintype();
        content_subtype = msg.get_content_subtype();
        if content_type == 'image':
            filename, blob = self.handle_image(msg)
            result.images[filename] = blob
        elif content_type == 'text':
            if content_subtype == 'plain':
                result.plain_content = self.handle_text(msg)
            elif content_subtype == 'html':
                result.html_content = self.handle_text(msg)
        elif content_type == 'multipart' and content_subtype == 'mixed':
            result.sender = msg.get('from')
            result.to = msg.get('to')
            result.subject = msg.get('subject')
            result.date = msg.get('date')
            
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
            
    def handle_msg(self, msg_file):
        from email.parser import Parser
        parser = Parser()
        result = Storage(images=dict())
        with open(msg_file) as fp:
            x = parser.parse(fp)
            items = x.walk()
            for item in items:
                self.handle_message_item(item, result)
        return result
        #with open(msg_file) as f:
            #msg = email.message_from_file(f)        
        #s = msg['Return-Path'][1:-1]
        #m = re.search(r'(.*)<(.+)>', s)
        #if m:
            #sender_name, sender_email = m.groups()
        #else:
            #sender_name, sender_email = "", s
        #what = msg['To'].split('@')[0]
        #subject = msg['Subject']
        #subject = base64.b64decode(subject)
        #payload = msg.get_payload()
        #if what in ['info', 'support']:
            #self.handle_support(what, msg, payload)
        #elif what == 'photos':
            #self.handle_photos(payload)
            
            
    def handle_support(self, what, msg, payload):
        item = payload.pop()
        while True:
            s = item.get_payload()
            s = base64.b64decode(s)
            if not payload:
                break
            item = payload.pop()
        

    def handle_photos(self, payload):
        photo_list = []
        item = payload.pop()
        text_html = ""
        while True:
            disposition = item['Content-Disposition']
            if not disposition:
                break
            coding = item['Content-Transfer-Encoding']
            content_type = item['Content-Type']
            m = re.search(r'filename\=\"(.+)\"', disposition)
            filename = m.group(1)
            s = item.get_payload()
            blob = base64.b64decode(s)
            save_uploaded_photo(file_name, blob, path_tail, user_id)
            crc = zlib.crc32(blob)
            name, ext = splitext(filename)
            output_filename = '{}{:x}{}'.format(self.output_folder, crc & 0xffffffff, ext)
            with open(output_filename, 'wb') as f:
                f.write(blob)
            photo_info = dict(crc=crc, output_filename=output_filename, filename=filename)
            photo_list.append(photo_info)
            item = payload.pop()
            if not item['Content-Disposition']:
                m = item.get_payload()
                text_html = m[1].get_payload()
                break
        return dict(sender_email=sender_email, sender_name=sender_name, text_html=text_html, photo_list=photo_list)
    
def test_collect_mail():
    email_photos_collector = EmailPhotosCollector(maildir='/home/haim/tmp/maildir/new', output_folder='/home/haim/tmp/photos/') 
    email_photos_collector.collect()
    
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