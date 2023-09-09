from .injections import inject
from distutils import dir_util
import os
from sys import platform
if platform == 'linux':
    import pwd

RESIZED  =        'orig'
ORIG    =        'oversize'
SQUARES =        'squares'
PROFILE_PHOTOS = 'profile_photos'

def url_folder(kind):
    request = inject('request')
    app = request.application
    app1 = app.split('__')[0]  # we want dev, test and www apps share the same photos
    h = 'https' if request.is_https else 'http'
    return '{h}://{host}/{app}/static/apps_data/{app1}/{kind}/'.format(h=h, host=request.env.http_host, app=app, app1=app1, kind=kind)


def local_folder(kind):
    request = inject('request')
    app = request.application.split('__')[0]  ## we want gbs__dev, gbs__test etc. all to use the same data
    path = f'/apps_data/{app}/{kind}/'
    if platform != 'linux':
        return path
    curr_uid = os.geteuid()
    uid = get_user_id()
    dir_util.mkpath(path)
    if curr_uid == 0:
        os.chown(path, uid, uid)
    return path

def local_cards_folder():
    request = inject('request')
    app = request.application
    path = f'/apps_data/cards/{app}/'
    return path

def url_cards_folder():
    request = inject('request')
    app = request.application
    host = request.env.http_host
    return f'cards.{host}/{app}/'

def system_folder():
    path = '/apps_data/system_data/'
    if platform != 'linux':
        return path
    curr_uid = os.geteuid()
    uid = get_user_id()
    dir_util.mkpath(path)
    if curr_uid == 0:
        os.chown(path, uid, uid)
    return path


def photos_folder(what):
    # what may be orig, squares or profile_photos.
    return url_folder('photos') + what + '/'


def images_folder():
    return url_folder('images')


def local_photos_folder(what):
    return local_folder('photos' + '/' + what)


def local_images_folder():
    return local_folder('images')


def get_user_id():
    request = inject("request")
    web2py_path = request.env.web2py_path
    if 'haim' in web2py_path:
        uname = "haim"
    else:
        uname = 'www-data'
    return pwd.getpwnam(uname).pw_uid

    
def safe_open(filename, mode):
    if platform == 'linux':
        curr_uid = os.geteuid()
        uid = get_user_id()
        f = open(filename, mode, encoding="utf-8")
        if curr_uid == 0:
            os.chown(filename, uid, uid)
    else:
        f = open(filename, mode, encoding="utf-8")
    return f

def url_video_folder():
    request = inject('request')
    app = request.application
    app1 = app.split('__')[0]  # we want dev, test and www apps share the same photos/videos
    h = 'https' if request.is_https else 'http'
    host = request.env.http_host
    return f'{h}://{host}/{app}/static/apps_data/{app1}/videos/'

def local_video_folder():
    request = inject('request')
    app = request.application.split('__')[0]  ## we want gbs__dev, gbs__test etc. all to use the same data
    path = '/apps_data/{app}/videos/'.format(app=app)
    if platform != 'linux':
        return path
    curr_uid = os.geteuid()
    uid = get_user_id()
    dir_util.mkpath(path)
    if curr_uid == 0:
        os.chown(path, uid, uid)
    return path


