import yagmail
import os

# import keyring
from injections import inject
from folders import system_folder


def email(to="", subject="", message="", sender=None):
    comment, log_exception = inject('comment', 'log_exception')
    if (not sender) or ('@' not in sender):
        request = inject('request')
        host = request.env.http_host
        if host.startswith('127'):
            host = "tol.life"
        app = request.application
        dept = sender if sender else 'info'
        sender = f"{dept}@{app}.{host}"
    # password = keyring.get_password("gmail.com", "lifestone2508")
    # the above fails because it asks for the protecting password but there is no user to answer
    password = os.environ.get('MAILPASS')
    password = '931632@Ha211224'
    comment(f"about to send email. pass: {password}")
    try:
        ###yag = yagmail.SMTP({"lifestone2508@gmail.com": sender}, password)
        ofile = system_folder() + 'tolife-auth.json'
        comment(f'yagmail. ofile is {ofile}')
        try:
            yag = yagmail.SMTP({"lifestone2508@gmail.com": sender}, oauth2_file=system_folder() + 'tolife-auth.json')
        except:
            yag = yagmail.SMTP({"lifestone2508@gmail.com": sender}, password)
    except:
        log_exception(f'failed to create yag')
        raise Exception('failed to create email sender')
    try:
        result = yag.send(to=to, subject=subject, contents=message)
    except:
        log_exception(f'failed to send')
        raise Exception('failed to send email')
    return result


def test():
    to = ['haimavni@gmail.com', 'hanavni@gmail.com']
    subject = "testing yagmail again and again"
    message = '''
        Hello there,<br><br>
        Please click <a href="haha.tol.life">here</a>
        '''
    # sender = "Info@tol.life"
    result = email(to=to, subject=subject, message=message)  # , sender=sender)
    print(f"the result is {result}")
    return result


if __name__ == "__main__":
    test()
