from words import remove_all_tags

def index():
    host = request.env.http_host
    app = request.application
    url_base = '/{app}/static/aurelia/index.html#/'.format(host=host,app=app)
    # temp. for the dev system
    if '8000' in host:
        host = "gbstories.org"
        url_base = 'http://{host}/{app}/static/aurelia/index.html#/'.format(host=host,app=app)
    ubase = f"https://{host}/{app}/"
    canonical = ubase + "searchable/"
    
    m_list = db((db.TblMembers.story_id==db.TblStories.id) & (db.TblStories.deleted!=True)).select(db.TblStories.name, db.TblMembers.id)
    # member_list = [A(r.TblStories.name, _href=url_base + "member-details/{}/*".format(r.TblMembers.id)) for r in m_list]
    member_list = [A(r.TblStories.name, _href=ubase + f"searchable/member/{r.TblMembers.id}") for r in m_list]

    p_list = db((db.TblPhotos.story_id==db.TblStories.id) & (db.TblStories.deleted!=True)).select(db.TblStories.name, db.TblPhotos.id, limitby=(0,20))
    photo_list = [A(r.TblStories.name, _href=url_base + "photos/{}/*".format(r.TblPhotos.id)) for r in p_list]
    
    s_list = db((db.TblStories.used_for==STORY4EVENT) & (db.TblStories.deleted != True)).select(db.TblStories.id, db.TblStories.name, db.TblStories.used_for, limitby=(0,10))    ##story_list = ['<a src="{id}">{name}</a>'.format(name=r.name, id=r.id) for r in story_list]
    story_list = [A(r.name, _href=url_base + "story-detail/{}/*?what=story".format(r.id)) for r in s_list]
    
    t_list = db((db.TblStories.used_for==STORY4TERM) & (db.TblStories.deleted != True)).select(db.TblStories.id, db.TblStories.name, db.TblStories.used_for, limitby=(0,10))    ##story_list = ['<a src="{id}">{name}</a>'.format(name=r.name, id=r.id) for r in story_list]
    term_list = [A(r.name, _href=url_base + "term-detail/{}/*?what=term".format(r.id)) for r in t_list]
    
    return dict(member_list=member_list, photo_list=photo_list, story_list=story_list, term_list=term_list, canonical=canonical)

def member():
    member_id = request.args[0]
    member = db(db.TblMembers.id==member_id).select().first()
    name = (member.first_name or "") + " " + (member.last_name or "")
    story_id = member.story_id
    if story_id:
        story_rec = db(db.TblStories.id==story_id).select().first()
        bio = story_rec.story
        bio = remove_all_tags(bio)
    else:
        bio = ""
    href = calc_href("member-details", member_id)
    link = A(name, _href=href)
    return dict(name=name, bio=bio,href=href,link=link)

def calc_href(what, id):
    host = request.env.http_host
    app = request.application
    r = app.find("__")
    if r > 0:
        app = app[:r]
    return f'https://{host}/{app}/aurelia#/{what}/{id}/*'

    