import smtplib, ssl

port = 465  # SSL standard port
my_pass = input("Type your password and press enter: ")
my_mail = "spivak.mark4@gmail.com"
from_mail = my_mail
#to_mail = "spivak4.mark@gmail.com"
to_mail = "haimavni@gmail.com"
message = "Subject: Trying send email by Python \n\n" + " I can send email by Python ! . \n "
message = message + " Have learned sending plain simple text, now will try something more comlicated \n"
message = message + " Confirm,please,receiving the mail "

context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(my_mail, my_pass)
    server.sendmail(from_mail, to_mail, message)




