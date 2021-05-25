import yagmail
import keyring

def send_email(to="", subject="", contents="", sender=""):
    password = keyring.get_password("gmail.com", "lifestone2508")
    yag = yagmail.SMTP({"lifestone2508@gmail.com": sender}, password)
    result = yag.send(to=to, subject=subject, contents=contents)
    return result
    
def test():
    to=['haimavni@gmail.com', 'hanavni@gmail.com']
    subject="testing yagmail again and again"
    contents= '''
        Hello there,<br><br>
        Please click <a href="haha.tol.life">here</a>
        '''
    sender = "Info@tol.life"
    result = send_email(to=to, subject=subject,contents=contents, sender=sender)
    print(f"the result is {result}")
