import datetime

s = str(datetime.datetime.now())[:16]

with open('/home/haim/deployment_folder/curr_version.txt', 'w') as f:
    f.write(s)
