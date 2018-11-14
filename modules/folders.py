from injections import inject

def url_folder(kind):
    request = inject('request')
    app = request.application.split('__')[0]  #we want dev, test and www apps share the same photos
    #app appears twice: one to reach static, the other is to separate different customers
    return 'http://{host}/{app}/static/gb_photos/{app}/{kind}/'.format(host=request.env.http_host, app=app, kind=kind)

def local_folder(kind):
    request = inject('request')
    app = request.application.split('__')[0]  ## we want gbs__dev, gbs__test etc. all to use the same data
    return '/gb_photos/{app}/{kind}/'.format(app=app, kind=kind)

