import sys

def main():
    app = sys.argv[1]
    service_name = '/etc/systemd/system/web2py-scheduler.service'
    with open(service_name, 'r') as f:
        txt = f.read()
    if '{},'.format(app) in text:
        return
    with open(service_name + '.bak', 'w') as f:
        f.write(txt)
    txt = txt.replace(' -K ', ' -K {},{},'.format(app, app))
    with open(service_name, 'w') as f:
        f.write(txt)

main()