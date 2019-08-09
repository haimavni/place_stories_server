import cgi
from my_cache import Cache
from langs import fix_utf8

#---------------------------------------------------------------------------
# Show Logs
#---------------------------------------------------------------------------

def log_Path():  #upper case to prevent collision with model function log_path
    path = 'applications' + URL(r=request, c='logs')
    r = path.rfind('/')
    return path[:r]

@serve_json
def log_file_list(vars):
    lst = sorted(os.listdir(log_Path()))
    log_files = [dict(fn=fn) for fn in lst]
    return dict(log_files=log_files)

@serve_json
def log_file_data(vars):
    fname = log_Path() + '/' + vars.file_name
    with open(fname, 'r') as f:
        text=f.read()
    data = fix_utf8(text)
    if not fname.endswith('html'):
        data = cgi.escape(data)
        data = XML(data.replace(' ', '&nbsp;').replace('\n', '<BR />'))
    return dict(log_html=data)

@serve_json
def delete_log_file(vars):
    filename = log_Path() + '/' + vars.file_name
    import os
    os.remove(filename)
    return dict()

def download_file():
    filename = '/'.join(request.args)
    fname = filename.split('/')[-1]
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(fname)    
    return response.stream(filename, chunk_size=4096)    

@serve_json
def download_log_file(vars):
    fname = vars.file_name
    filename = log_Path() + '/' + fname
    return dict(file_path=filename)


