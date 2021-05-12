import yagmail

#to_mail = "spivak4.mark@gmail.com"
to_mail = "haimavni@gmail.com"
from_mail = "spivak.mark4@gmail.com"
my_mail = from_mail
subject = "Yagmail test with attachment"
body = "Sending mail with Yagmail"
attachment = "sendmail_yag.py"

yag = yagmail.SMTP(my_mail)
yag.send(
    to_mail,
    subject,
    body,
    attachment
)