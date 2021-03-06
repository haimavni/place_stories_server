from injections import inject
from distutils import dir_util
import os
import pwd

def url_folder(kind):
    request = inject('request')
    app = request.application.split('__')[0]  #we want dev, test and www apps share the same photos
    #app appears twice: one to reach static, the other is to separate different customers
    h = 'https' if request.is_https else 'http'
    return '{h}://{host}/{app}/static/gb_photos/{app}/{kind}/'.format(h=h, host=request.env.http_host, app=app, kind=kind)

def local_folder(kind):
    request = inject('request')
    app = request.application.split('__')[0]  ## we want gbs__dev, gbs__test etc. all to use the same data
    path = '/gb_photos/{app}/{kind}/'.format(app=app, kind=kind)
    curr_uid = os.geteuid()
    uid = get_user_id()
    dir_util.mkpath(path)
    if curr_uid == 0:
        os.chown(path, uid, uid)
    return path

def system_folder():
    path = '/gb_photos/system_data/'
    curr_uid = os.geteuid()
    uid = get_user_id()
    dir_util.mkpath(path)
    if curr_uid == 0:
        os.chown(path, uid, uid)
    return path

def photos_folder(what="orig"):
    #what may be orig, squares or profile_photos.
    return url_folder('photos') + what + '/'

def images_folder():
    return url_folder('images')

def local_photos_folder(what="orig"):
    #what may be orig, squares,images or profile_photos. (images is for customer-specific images such as logo)
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
    curr_uid = os.geteuid()
    uid = get_user_id()
    f = open(filename, mode)
    if curr_uid == 0:
        os.chown(filename, uid, uid)
    return f   
            
