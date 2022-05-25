### import yagmail
from redmail import gmail

import os

# import keyring
from injections import inject
from folders import system_folder

def email(receivers=["haimavni@gmail.com"], subject="message from tol.life", message="", sender=None)    :
    gmail.username = 'lifestone2508@gmail.com' # Your Gmail address
    gmail.password = 'wdxrovalrscyksty'
    if isinstance(receivers, str):
        receivers = [receivers]
    if not sender:
        sender = get_app_title()
    if not sender:
        sender = 'info@tol.life'
    result = gmail.send(
        sender=sender + f'<lifestone2508@gmail.com>',
        subject=subject,
        receivers=receivers,
        html=message
    )

def get_app_title():
    db = inject('db')
    rec = db(db.TblConfiguration.id==1).select(db.TblConfiguration.app_title).first()
    return rec.app_title or 'Our Stories'


def test():
    receivers = ['haimavni@gmail.com', 'hanavni@gmail.com']
    subject = "testing redmail"
    message = '''
        Hello there,<br><br>
        Please click <a href="haha.tol.life">here</a>
        '''
    # sender = "Info@tol.life"
    result = email(receivers=receivers, subject=subject, message=message)  # , sender=sender)
    #print(f"the result is {result}")
    return result


if __name__ == "__main__":
    test()
