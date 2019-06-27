def index():
    m_list = db((db.TblMembers.story_id==db.TblStories.id) & (db.TblStories.deleted!=True)).select(db.TblStories.name, db.TblMembers.id, limitby=(0,20))
    member_list = [A(r.TblStories.name, _href="https://gbstories.org/gbs__test/static/aurelia/index.html#/member-details/{}/*".format(r.TblMembers.id)) for r in m_list]
    p_list = db((db.TblPhotos.story_id==db.TblStories.id) & (db.TblStories.deleted!=True)).select(db.TblStories.name, db.TblPhotos.id, limitby=(0,20))
    photo_list = [A(r.TblStories.name, _href="https://gbstories.org/gbs__test/static/aurelia/index.html#/photos/{}/*".format(r.TblPhotos.id)) for r in p_list]
    s_list = db((db.TblStories.used_for==STORY4EVENT) & (db.TblStories.deleted != True)).select(db.TblStories.id, db.TblStories.name, db.TblStories.used_for, limitby=(0,10))    ##story_list = ['<a src="{id}">{name}</a>'.format(name=r.name, id=r.id) for r in story_list]
    story_list = [A(r.name, _href="https://gbstories.org/gbs__test/static/aurelia/index.html#/story-detail/{}/*?what=story".format(r.id)) for r in s_list]
    t_list = db((db.TblStories.used_for==STORY4TERM) & (db.TblStories.deleted != True)).select(db.TblStories.id, db.TblStories.name, db.TblStories.used_for, limitby=(0,10))    ##story_list = ['<a src="{id}">{name}</a>'.format(name=r.name, id=r.id) for r in story_list]
    term_list = [A(r.name, _href="https://gbstories.org/gbs__test/static/aurelia/index.html#/term-detail/{}/*".format(r.id)) for r in t_list]
    return dict(member_list=member_list, photo_list=photo_list, story_list=story_list, term_list=term_list)