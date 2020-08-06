import distutils.dir_util
from folders import local_folder

def log_path():
    path = local_folder('logs')
    distutils.dir_util.mkpath(path)
    return path
