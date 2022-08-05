#!/usr/bin/env python

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import time

def main():

    message = MIMEMultipart("alternative")
    message["Subject"] = "test"
    message["From"]    = "info@gbstories.org"
    message["To"]      = "haimavni@gmail.com"

    text = "hello world"

    html = '''<strong>Hellow</strong>world!'''

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        print(("send message to {to}".format(
             to = message["To"]
         )))
        server = smtplib.SMTP("localhost")
        server.sendmail(
             message["From"],
             message["To"],
             message.as_string()
         )
        server.quit()
    except smtplib.SMTPException:
        print("e-mail send error")
    time.sleep(5)

if __name__ == "__main__":
    main()

