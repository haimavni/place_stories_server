from langs import fix_utf8


# ---------------------------------------------------------------------------
# Show Logs
# ---------------------------------------------------------------------------

def logs_path():
    return local_folder('logs')


def logs_url():
    return url_folder('logs')


@serve_json
def log_file_list(vars):
    lst = sorted(os.listdir(logs_path()))
    log_files = [dict(fn=fn) for fn in lst]
    return dict(log_files=log_files)


@serve_json
def log_file_data(vars):
    # noinspection SpellCheckingInspection
    fname = logs_path() + '/' + vars.file_name
    with open(fname, 'r', encoding="utf-8") as f:
        text = f.read()
    data = fix_utf8(text)
    if not fname.endswith('html'):
        # data = cgi.escape(data)
        data = XML(data.replace(' ', '&nbsp;').replace('\n', '<BR />'))
    return dict(log_html=data)


@serve_json
def delete_log_file(vars):
    filename = logs_path() + '/' + vars.file_name
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
    filename = logs_url() + '/' + fname
    return dict(file_path=filename)
