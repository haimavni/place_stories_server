from injections import inject
import datetime


def create_member_item(member_id):
    request = inject('request')
    host = request.env.http_host
    app = request.application
    now = datetime.datetime.now()
    now = now.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    item = f'''
<url>
  <loc>https://{host}/{app}/searchable/member/{member_id}</loc>
  <lastmod>{now}</lastmod>
  <priority>0.9</priority>
</url>
'''
    return item

def create_sitemap():
    db, request, STORY4MEMBER, comment = inject('db', 'request', 'STORY4MEMBER', 'comment')
    host = request.env.http_host
    app = request.application
    lst = db((db.TblStories.used_for==STORY4MEMBER)&(db.TblStories.id==db.TblMembers.story_id)).select(db.TblMembers.id)
    member_list = [rec.id for rec in lst]
    # comment(f'inside emit bio items: {member_list}')
    header = '''
<?xml version="1.0" encoding="UTF-8"?>
<urlset
      xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
'''
    fname = f'/apps_data/{app}/sitemap.xml'
    # comment(f'writing to {fname}')
    # comment(f'header: {header}')
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(header)
        # comment(f'header was written to {fname}')
        for mid in member_list:
            item = create_member_item(mid)
            f.write(item)
        f.write('</urlset>')
    
    url = f"https://{host}/{app}/static/apps_data/{app}/sitemap.xml"
    return url
