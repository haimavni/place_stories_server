# import smtplib
 
# # creates SMTP session
# s = smtplib.SMTP('smtp.gmail.com', 587)
 
# # start TLS for security
# s.starttls()
 
# # Authentication
# s.login("securesally@gmail.com", "jwgqycesegkrbzuz")
 
# # message to be sent
# message = "Message_you_need_to_send"
 
# # sending the mail
# s.sendmail("sender_email_id", "receiver_email_id", message)
 
# # terminating the session
# s.quit()

import smtplib
import ssl
from email.message import EmailMessage
from misc_utils import get_env_var

def send_email():
    msg = EmailMessage()
    port = 587
    host = "smtp.gmail.com"
    sender = "lifestories2508@gmail.com"
    password = get_env_var("MAIL_PASSWORD")

    msg['From'] = sender
    msg['To'] = ["haimavni@gmail.com", "hanavni@gmail.com"]
    msg['Subject'] = "Test email subject"
    msg.set_content("Test email content")

    # Create a secure SSL context
    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

send_email()        