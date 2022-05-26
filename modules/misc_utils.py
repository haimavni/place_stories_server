from sys import platform
if platform == 'linux':
    from pwd import getpwnam, getpwuid

import os, stat
import getpass
from .injections import inject
from operator import attrgetter
import qrcode
from folders import local_folder, url_folder

def find_owner(filename):
    return getpwuid(os.stat(filename).st_uid).pw_name

def fix_log_owner(log_file_name):
    if platform != 'linux':
        return
    path, fname = os.path.split(log_file_name)
    curr_user = getpass.getuser()
    if curr_user != 'root':
        return
    file_owner = find_owner(log_file_name)
    if file_owner != 'root':
        return
    try:
        request = inject('request')
        parts = request.folder.split('/')
        if len(parts) >= 3:
            u = parts[2]
        else:
            u = 'haim'
        w_rec = getpwnam(u)
        wuid, wgid = w_rec.pw_uid, w_rec.pw_gid
        if file_owner != u:
            os.chown(log_file_name, wuid, wgid)
            os.chmod(log_file_name, stat.S_IRGRP | stat.S_IWGRP | stat.S_IREAD | stat.S_IWRITE | stat.S_IROTH)
    except Exception as e:
        path, fname = os.path.split(log_file_name)
        with open(path + '/' + 'fix_log_owner_failed.log', 'a') as f:
            f.write('folder: ' + request.folder + ' log name: ' + log_file_name + ' error: ' + str(e) + '\n')

def multisort(xs, specs):
    for key, reverse in reversed(specs):
        xs.sort(key=attrgetter(key), reverse=reverse)
    return xs

def make_qr_code(txt, name='qrcode'):
    img = qrcode.make(txt)
    path = local_folder('temp')
    filename = path + name + ".png"
    img.save(filename)
    download_url = url_folder("temp") + name + '.png'
    return dict(download_url=download_url)

if __name__ == '__main__':
    fname = '/home/haim/aurelia-gbs/server/tol_server/logs/log_all.log'
    fix_log_owner(fname)

def make_qr_code1(txt, name='qrcode'):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(txt)
    img = qr.make(fit=True)
    path = local_folder('temp')
    filename = path + name + ".png"
    img.save(filename)
    download_url = url_folder("temp") + name + '.png'
    return dict(download_url=download_url)

    ##img = qr.make_image(fill_color="black", back_color="white")
