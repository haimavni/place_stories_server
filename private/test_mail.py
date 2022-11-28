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

def send_email():
    msg = EmailMessage()
    port = 587
    host = "smtp.gmail.com"
    sender = "lifestone2508@gmail.com"
    password = "jwgqycesegkrbzuz"

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