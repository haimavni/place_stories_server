import yagmail

# import keyring
from injections import inject


def email(to="", subject="", message="", sender=None):
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
    password = "931632#Ha2104"
    yag = yagmail.SMTP({"lifestone2508@gmail.com": sender}, password)
    result = yag.send(to=to, subject=subject, contents=message)
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


if __name__ == "__main__":
    test()
