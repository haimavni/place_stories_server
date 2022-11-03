import os

def error_link(err_code):
    host = request.env.http_host
    app =  request.application
    err_url = f'/admin/default/ticket/{app}/{err_code}'
    return err_url

def index():
    app = request.application
    dir = f'applications/{app}/errors'
    err_list = os.listdir(dir)
    err_list = sorted(err_list, reverse=True)
    result = '<ul>'
    for err in err_list:
        url = error_link(err)
        item = f'<li><a href={url} target="blank">{err}</a></li>'
        result += item
    result += '</ul>'
    return result

   
   
