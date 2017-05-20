from gluon.storage import Storage
settings = Storage()

settings.migrate = True
settings.title = 'Cfind'
settings.subtitle = 'powered by web2py'
settings.author = 'Haim Avni'
settings.author_email = 'haimavni@gmail.com'
settings.keywords = ''
settings.description = 'Social Networks Monitor'
settings.layout_theme = 'GreenandPlain'
settings.database_uri = 'sqlite://storage.sqlite'
settings.security_key = '30c856a8-9889-44bd-940a-dece05fa7f1c'
settings.email_server = 'localhost'
settings.email_sender = 'support@gbs.co.il(Givat-Brenner Stories)'
settings.email_login = ''
settings.login_method = 'local'
settings.login_config = ''
settings.plugins = ['attachments', 'datatable', 'dropdown', 'wiki', 'comments', 'locking', 'mmodal', 'jqmobile', 'google_checkout', 'tagging', 'mediaplayer', 'latex', 'clickatell', 'simple_comments', 'rating', 'utils', 'gmap', 'markitup', 'jqgrid', 'multiselect', 'translate', 'sortable']
