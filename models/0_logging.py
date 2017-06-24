import distutils.dir_util

def log_path():
    path = 'applications/' + request.application + '/logs/'
    distutils.dir_util.mkpath(path)
    return path
