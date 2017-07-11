import email
import base64
import re
import zlib
from os import listdir
from os.path import isfile, join, splitext

class EmailPhotosCollector:
    
    def __init__(self, maildir, output_folder):
        self.output_folder = output_folder
        self.maildir = maildir #'/home/photos/Maildir'
        self.photo_collection = []
        
    def collect(self):
        msg_list = [join(self.maildir, f) for f in listdir(self.maildir) if isfile(join(self.maildir, f))]
        for msg_file in msg_list:
            self.handle_msg(msg_file)
            
    def handle_msg(self, msg_file):
        with open(msg_file) as f:
            msg = email.message_from_file(f)        
        s = msg['Return-Path'][1:-1]
        m = re.search(r'(.*)<(.+)>', s)
        sender_name, sender_email = m.groups()
        subject = msg['Subject']
        payload = msg.get_payload()
        photo_list = []
        item = payload.pop()
        while True:
            disposition = item['Content-Disposition']
            coding = item['Content-Transfer-Encoding']
            content_type = item['Content-Type']
            s = item.get_payload()
            blob = base64.b64decode(s)
            crc = zlib.crc32(blob)
            m = re.search(r'filename\=\"(.+)\"', disposition)
            filename = m.group(1)
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
    
def test():
    email_photos_collector = EmailPhotosCollector(maildir='/home/haim/tmp/maildir/', output_folder='/home/haim/tmp/photos/') 
    email_photos_collector.collect()
    
if __name__ == "__main__":
    # execute only if run as a script
    test()  
        