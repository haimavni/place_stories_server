# -*- coding: utf-8 -*-

from porting.create_old_db_mappings import table_fields, csv_name_to_table_name, get_records, csv_name_to_table_name
from glob import glob
import re
from photos_support import scan_all_unscanned_photos, fit_all_sizes, local_photos_folder
import random
from words import extract_tokens, guess_language, create_word_index, read_words_index
from html_utils import clean_html
import os, time
from stories_manager import Stories
from folders import RESIZED, ORIG, SQUARES, PROFILE_PHOTOS

def port_old_db():
    folder = request.vars.folder or 'gbs-bkp-jun17'
    path = base_app_dir + 'private/{}/'.format(folder)
    lst = glob(path + '*.csv')
    for csv_name in lst:
        table_name = csv_name_to_table_name(csv_name)
        tbl = db[table_name]
        for rec in get_records(csv_name):
            tbl.insert(**rec)
    return 'Porting db finished'

#mappings for conversion of old (IIDD) refs to native refs (id)

dblinks = dict(    
    TblEventMembers=['EventID', 'MemberID'],
    TblEventPhotos=['EventID', 'PhotoID'],
    TblEvents=['TypeID', 'ObjectID', 'StatusID'],
    TblMemberConnections=['MemberID', 'ConnectToMemberID', 'ConnectionTypeID'],
    TblMemberPhotos=['MemberID', 'PhotoID'],
    TblMembers=['ObjectID', 'StatusID'],
    TblPhotos=['ObjectID', 'StatusID'],
    TblTerms=['InventedByMemberID', 'ObjectID', 'StatusID']
)    

map_dblink_to_table_name = dict(
    EventID='TblEvents',
    MemberID='TblMembers',
    PhotoID='TblPhotos',
    TypeID='TblEventTypes',
    ObjectID='TblObjects',
    StatusID='TblStatuses',
    ConnectToMemberID='TblMembers',
    ConnectionTypeID='TblFamilyConnectionTypes',
    InventedByMemberID='TblMembers'
)
def convert_to_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def convert_IDrefs():
    for tbl in sorted(dblinks):
        flds = dblinks[tbl]
        fldsp = flds +['id']
        table = db[tbl]
        fields = [table[fld] for fld in flds] 
        fieldsp = [table[fld] for fld in fldsp]
        for rec in db(table).select(*fieldsp):
            u = {}
            for f in flds:
                new_fld_name = f[:-2] + '_id'
                IIDD = rec[f]
                if not IIDD:
                    continue
                if IIDD <= 0:
                    continue
                other_table_name = map_dblink_to_table_name[f]
                other_table = db[other_table_name]
                other_field = other_table['IIDD']
                other_id_field = other_table['id']
                i = db(other_field==IIDD).select(*[other_id_field]).first().id
                u[new_fld_name] = i
            db(table.id==rec.id).update(**u)
        pass
    return 'Finished conversion of all IDs'

def port_family_connections():
    lst = db(db.TblMemberConnections.ConnectionTypeID==1).select()
    for rec in lst:
        member_id = rec.Member_id
        father_id = rec.ConnectToMember_id
        db(db.TblMembers.id==member_id).update(father_id=father_id)
    lst = db(db.TblMemberConnections.ConnectionTypeID==2).select()
    for rec in lst:
        member_id = rec.Member_id
        mother_id = rec.ConnectToMember_id
        db(db.TblMembers.id==member_id).update(mother_id=mother_id)
    return 'Finished conversion of parents'

def consolidate_stories():
    lst = db(db.TblMembers.LifeStory != '').select(db.TblMembers.LifeStory, db.TblMembers.id)
    for rec in lst:
        story_id = db.TblStories.insert(story=rec.LifeStory, used_for=STORY4MEMBER)
        db(db.TblMembers.id==rec.id).update(story_id=story_id, LifeStory='', LifeStoryNoHtml='')

    lst = db(db.TblEvents.Description != '').select(db.TblEvents.Description, db.TblEvents.id)
    for rec in lst:
        story_id = db.TblStories.insert(story=rec.Description, used_for=STORY4EVENT)
        db(db.TblEvents.id==rec.id).update(story_id=story_id, Description='', DescriptionNoHtml='')

    lst = db((db.TblPhotos.Description != '') & (db.TblPhotos.deleted!=True)).select(db.TblPhotos.Description, db.TblPhotos.id)
    for rec in lst:
        story_id = db.TblStories.insert(story=rec.Description, used_for=STORY4PHOTO)
        db(db.TblPhotos.id==rec.id).update(story_id=story_id, Description='', DescriptionNoHtml='')

    lst = db(db.TblTerms.Background != '').select()
    for rec in lst:
        story_id = db.TblStories.insert(story='<div class="term-translation">' + rec.TermTranslation + '</div>' +
                                        '<div class="term-background">' + rec.Background + '</div>', 
                                        used_for=STORY4TERM)
        db(db.TblTerms.id==rec.id).update(story_id=story_id, Background='', BackgroundNoHtml='', TermTranslation='')

    return 'Finished consolidation of stories'

def to_hebrew(s):
    alef = 'א'
    tav = 'ת'
    alef = alef.decode('utf8')
    tav = tav.decode('utf8')
    result = ''
    for c in s:
        if alef <= c <= tav:
            result += c
    return result.strip()

def name_stories():
    lst = db(db.TblStories.id==db.TblEvents.story_id).select()
    for i, rec in enumerate(lst):
        story = rec.TblStories.story.decode('utf8')
        name = rec.TblEvents.Name
        source = rec.TblEvents.SSource
        if not name:
            words = extract_tokens(story)
            name = ' '.join(words[:6]).strip()
            if name:
                name += "..."
        db(db.TblStories.id==rec.TblStories.id).update(name=name, source=source)

    lst = db(db.TblStories.used_for==STORY4MEMBER).select()
    for i, rec in enumerate(lst):
        story = rec.story.decode('utf8')
        name = rec.name
        if (not name) or name.endswith("..."):
            words = extract_tokens(story)
            name = ' '.join(words[:6]).strip()
            if name:
                name += "..."
        db(db.TblStories.id==rec.id).update(name=name, source="")

    lst = db(db.TblStories.id==db.TblTerms.story_id).select()
    for i, rec in enumerate(lst):
        story = rec.TblStories.story.decode('utf8')
        name = rec.TblTerms.Name
        author = rec.TblTerms.InventedBy
        author_id = rec.TblTerms.InventedByMember_id or 1
        if not name:
            words = extract_tokens(story)
            name = ' '.join(words[:6]).strip()
            if name:
                name += "..."
        db(db.TblStories.id==rec.TblStories.id).update(name=name, source=author)

    lst = db(db.TblStories.id==db.TblPhotos.story_id).select()
    for i, rec in enumerate(lst):
        story = rec.TblStories.story.decode('utf8')
        name = rec.TblPhotos.Name
        if not name:
            words = extract_tokens(story)
            name = ' '.join(words[:6]).strip()
            if name:
                name += "..."
        db(db.TblStories.id==rec.TblStories.id).update(name=name, source="")                

    return 'Finished naming stories'

def fix_photo_location_case():
    idx = dict()
    n_missing = 0
    n_fixed = 0
    with open('applications/' + request.application + '/static/apps_data/tmp.lst') as f:
        for s in f:
            s = s.strip()[2:]
            idx[s.lower()] = s
    lst = db(db.TblPhotos).select()
    for rec in lst:
        s = rec.LocationInDisk
        if s.lower() not in idx:
            rec.update_record(photo_missing=True)
            n_missing += 1
        elif s != idx[s.lower()]:
            rec.update_record(LocationInDisk=idx[s.lower()])
            n_fixed += 1
    return '{} missing, {} fixed'.format(n_missing, n_fixed)

def guess_names():
    lst = db(db.TblMembers).select()
    n_fixed = 0
    for rec in lst:
        if rec.first_name:
            continue
        name = rec.Name
        name = re.sub(r'\(.*\)', '', name)
        parts = name.split()
        rec.update_record(first_name = parts[0], last_name = ' '.join(parts[1:]))
        n_fixed += 1
    return '{} names were guessed'.format(n_fixed)

def rename_locations():
    for rec in db(db.TblPhotos).select():
        rec.update_record(photo_path="ported/" + rec.LocationInDisk)
        
def init_all_photos():
    db(db.TblPhotos).update(crc=None, photo_missing=False)
    db.commit()
    
def scan_photos():
    return scan_all_unscanned_photos()

def guess_photographer(location):
    candidates = dict(
        givon = "גבעון כהן",
        hanan = "חנן בהיר",
        lipman = "ולטר ליפמן",
        micha = "מיכה אבני",
        nanan = "חנן בהיר", #assuming this is a typo
        vertheim = "אליעזר ורטהיים",
        yok = "יוקי שטל"
    )
    location = location.lower()
    for p in candidates:
        if p in location:
            return candidates[p]
    return None

def collect_photographers():
    ###db.TblPhotographers.truncate('RESTART IDENTITY CASCADE')
    lst = db((db.TblPhotos.width>0) & (db.TblPhotos.deleted!=True)).select()
    for rec in lst:
        if not rec.Photographer:
            rec.Photographer = guess_photographer(rec.LocationInDisk)
        if not rec.Photographer:    
            continue
        name = rec.Photographer.strip()
        p = db(db.TblPhotographers.name==name).select().first()
        if p:
            i = p.id
        else:
            i = db.TblPhotographers.insert(name=name)
        rec.update_record(photographer_id=i)
    db.commit()

def find_duplicate_photos():
    dic = {}
    dups = {}
    lst = db((db.TblPhotos.width>0)&(db.TblPhotos.deleted!=True)).select()
    for rec in lst:
        if rec.crc in dic:
            dic[rec.crc].append(rec.id)
            dups[rec.crc] = dic[rec.crc]
        else:
            dic[rec.crc] = [rec.id]
    z = len(dups)
    if z > 0:
        y = z

def string_date_to_date(s):
    p = "שנות ה"
    day = 1
    mon = 1
    year = 1
    raw_str = '????-??-??'
    if s:
        s = s.replace(' ', '')
        m = re.search(r'(\d{4})\-(\d{4})', s)
        if m:
            return ('lifespan', m.group(1), m.group(2))
        if p in s:
            m = re.search(r'(\d{1,2})', s)
            if m:
                year = m.groups()[0]
                if len(year) < 2:
                    year += '0'
                year = 1900 + int(year)
                raw_str = str(year) + '-??-??'
        else:
            m = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', s)
            if m:
                day, mon, year = m.groups()
                day, mon, year = (int(day), int(mon), int(year))
                raw_str = '{year:04}-{mon:02}-{day:02}'.format(year=year, mon=mon, day=day)
            else:
                m = re.search(r'(\d{1,2})[./](\d{4})', s)
                if m:
                    mon, year = m.groups()
                    mon, year = (int(mon), int(year))
                    raw_str = '{year:04}-{mon:02}-??'.format(year=year, mon=mon)
                else:
                    m = re.search(r'(\d{4})', s)
                    if m:
                        year = int(m.groups()[0])
                        raw_str = '{year:04}-??-??'.format(year=year)

    return ('singledate', datetime.date(year=year, month=mon, day=day), raw_str)

def dash_to_camel(s):
    b = True
    t = ""
    for c in s:
        if b:
            c = c.upper()
            b = False
        if c == "_":
            b = True
            continue
        t += c
    return t

def port_all_dates():
    tbls = db.tables()
    for tbl in tbls:
        table = db[tbl]
        flds = table.fields()
        flds = [f for f in flds if f.endswith('_str')]
        if not flds:
            continue
        fields = {}
        for fld in flds:
            date_field = fld[:-4]
            old_date_field = dash_to_camel(date_field)
            fields[old_date_field] = date_field
        for rec in db(table).select():
            data = {}
            for f in fields:
                if f.endswith('Death'):
                    continue
                old_date_value = rec[f]
                kind, val1, val2 = string_date_to_date(old_date_value)
                if kind == 'singledate':
                    new_date_value, new_date_str = (val1, val2)
                    k = fields[f]
                    data[k] = new_date_value
                    data[k + '_str'] = new_date_str
                else:
                    birth, death = val1, val2
                    k = fields[f]
                    data[k] = datetime.datetime(day=1, month=1, year=int(val1))
                    data[k + '_str'] = val1 + "-??-??"
                    k1 = k.replace('birth', 'death')
                    data[k1] = datetime.datetime(day=1, month=1, year=int(val2))
                    data[k1 + '_str'] = val2 + "-??-??"
            rec.update_record(**data)
    return 'port_all_dates done!'

def port_photos_date():
    lst = db((db.TblPhotos.width>0) & (db.TblPhotos.photo_date==None)).select(db.TblPhotos.id, db.TblPhotos.PhotoDate, db.TblPhotos.photo_date, db.TblPhotos.photo_date_accuracy)
    for rec in lst:
        date, date_str = string_date_to_date(rec.PhotoDate)
        db(db.TblPhotos.id==rec.id).update(photo_date=date, photo_date_accuracy=accuracy)
    db.commit()

def collect_topics(topic_collection, tbl_name):
    tbl = db[tbl_name]
    link_fld_id = tbl_name[3:-1].lower() + '_id'
    this_collection = dict()
    code = tbl_name[3]
    q = tbl['KeyWords'] != ""
    lst = db(q).select()
    for rec in lst:
        s = rec.KeyWords
        if not s:
            continue
        topics = s.split(',')
        for topic in topics:
            topic = topic.strip()
            if topic in topic_collection:
                idx = topic_collection[topic]
                if topic not in this_collection:
                    r = db(db.TblTopics.id==idx).select().first()
                    if code not in r.usage:
                        r.update_record(usage = r.usage + code)
                    this_collection[topic] = 1
            else:
                topic_collection[topic] = idx = db.TblTopics.insert(name=topic, usage=code)
            dic = dict(
                item_id=rec.id,
                topic_id=idx,
                story_id=rec.story_id,
                item_type=tbl_name[3]
            )
            db.TblItemTopics.insert(**dic)

def port_topics():            
    db.TblTopics.truncate('RESTART IDENTITY CASCADE')
    db.TblItemTopics.truncate('RESTART IDENTITY CASCADE')
    topic_collection = dict()
    for tbl_name in ['TblPhotos', 'TblEvents', 'TblMembers']:
        collect_topics(topic_collection, tbl_name)
    x = len(topic_collection)

def create_random_photo_keys():
    for rec in db(db.TblPhotos).select():
        key = random.randint(1, 100)
        rec.update_record(random_photo_key=key)
    db.commit()

def fit_all_photo_sizes():
    fit_all_sizes()

def set_stories_language():
    dic = {}
    for rec in db(db.TblStories).select():
        lang = guess_language(rec.story)
        if lang not in dic:
            dic[lang] = 0
        dic[lang] += 1
        rec.update_record(language=lang)
    x = len(dic)
    z = x

def port_from_old_db():
    if db(db.TblMembers).count() > 0:
        return "Database already ported"
    try:
        comment('starting port old db')
        port_old_db()
        comment('start convert IDrefs')
        convert_IDrefs() 
        comment('start port family connections')
        port_family_connections()
        comment('start consolidate stories')
        consolidate_stories()
        comment('start name stories')
        name_stories()
        guess_names()
        comment("start scan photos")
        fix_photo_location_case()
        rename_locations()
        scan_photos()
        comment('start fixing photo location case')
        ###db.commit()
        collect_photographers()
        fit_all_photo_sizes()
        port_all_dates()
        port_topics()
        create_random_photo_keys()
        set_stories_language()
        ####calculate_story_lengths()
        comment("start collecting word statistics")
        collect_word_statistics()
        comment("start calculating visibility")
        calc_members_visibility()
        comment('Porting done')
    except Exception as e:
        log_exception('Porting old db failed')
        return 'Porting old db failed: ' + e.message
    db.commit()
    return "Old db was converted and modified"

def collect_word_statistics():
    create_word_index()

def get_word_index():
    dic = read_words_index()

def calc_members_visibility():
    dic = dict()
    for member in db(db.TblMembers).select():
        mem_id = member.id
        dic[mem_id] = dict(photo_count=0, story_count=1 if member.story_id != None else 0)
        member.update_record(visibility=VIS_NOT_READY)
    for rec in db(db.TblMemberPhotos).select():
        mem_id = rec.Member_id
        if not mem_id: #should not happen, but it did...
            continue
        dic[mem_id]['photo_count'] += 1
    for rec in db(db.TblEventMembers).select():
        mem_id = rec.Member_id
        if not mem_id:
            continue
        dic[mem_id]['story_count'] += 1
    for mem_id in dic:
        scores = dic[mem_id]
        if scores['photo_count'] > 6 or scores['story_count'] > 3:
            vis = VIS_HIGH
        elif scores['photo_count'] > 0 or scores['story_count'] > 0:
            vis = VIS_VISIBLE
        else:
            vis = 0
        if vis:
            db(db.TblMembers.id==mem_id).update(visibility=vis)
            
def blank_ref(m):
    s = m.group(0)
    if '_blank' in s:
        return s
    s = s[:-1] + ' target="_blank"' + s[-1]
    return s
          
def blank_refs(html):
    pat = r'<a .*?>'
    s = re.sub(pat, blank_ref, html)
    return s

def blank_all_refs():
    lst = db(db.TblStories.story.like("%href=%")).select()
    for rec in lst:
        html = blank_refs(rec.story)
        rec.update_record(story=html)
    db.commit()
    
class RefsFixer:
    base_url = request.env.http_orign or request.env.http_host
    app = request.application
    app_area = app.split('__')[0]
    ###photo_ref_format = '<img src="' + base_url + '/{app_area}/static/apps_data/{app_area}/photos/orig/'.format(app_area=app_area) + '{path}">'
    photo_ref_format = '<a href="/{app}/static/aurelia/index.html#/photos/'.format(app=app) + '{photo_id}/*">'
    member_ref_format = '<a href="/{app}/static/aurelia/index.html#/member-details/'.format(app=app) + '{mem_id}/*">'
    story_ref_format = '<a href="/{app}/static/aurelia/index.html#/story-detail/'.format(app=app) + '{sid}/*?what=story">'
    term_ref_format = '<a href="/{app}/static/aurelia/index.html#/term-detail/'.format(app=app) + '{sid}/*?what=story">'
    
    def __init__(self):
        self.refs_map = dict(member = {}, 
                             event = {}, 
                             photo = {}, 
                             term = {})
        self.map_old_event_ids_to_story_ids()
        self.map_old_photo_ids_to_new_photo_ids()
        self.map_old_member_ids_to_new_member_ids()
        self.map_old_term_ids_to_new_terms_ids()
        self.num_errors = 0
        self.counter = dict()

    def map_old_event_ids_to_story_ids(self):
        dic = dict()
        lst = db(db.TblEvents.story_id==db.TblStories.id).select()
        for rec in lst:
            dic[rec.TblEvents.IIDD] = rec.TblStories.id
        self.refs_map['event'] = dic
    
    def map_old_photo_ids_to_new_photo_ids(self):
        dic = dict()
        lst = db(db.TblPhotos).select()
        for rec in lst:
            dic[rec.IIDD] = rec.id
        self.refs_map['photo'] = dic
    
    def map_old_member_ids_to_new_member_ids(self):
        dic = dict()
        lst = db(db.TblMembers).select()
        for rec in lst:
            dic[rec.IIDD] = rec.id
        self.refs_map['member'] = dic
            
    def map_old_term_ids_to_new_terms_ids(self):
        dic = dict()
        lst = db(db.TblTerms).select()
        for rec in lst:
            dic[rec.IIDD] = rec.story_id
        self.refs_map['term'] = dic

    def replace_ref(self, m):
        s = m.group(0)
        what = m.group(1)
        if what not in self.counter:
            self.counter[what] = 0
        self.counter[what] += 1
        comment(f"ref type {what}")
        ref_id = m.group(3)
        ref_id = int(ref_id)
        try:
            if what == 'member':
                return RefsFixer.member_ref_format.format(mem_id=self.refs_map['member'][ref_id])
            if what == 'event':
                return RefsFixer.story_ref_format.format(sid=self.refs_map['event'][ref_id])
            if what == 'term':
                return RefsFixer.story_ref_format.format(sid=self.refs_map['term'][ref_id])
            if what == 'photo':
                return RefsFixer.photo_ref_format.format(path=self.refs_map['photo'][ref_id])
        except Exception as e:
            self.num_errors += 1
            pass
        #todo: implement the transformation
        comment(f"ERROR in story {self.curr_story_id}")
        return m.group(0)
    
    def fix_old_site_refs(self):
        q = db.TblStories.story.like("%givat-brenner.co.il%") & \
            (db.TblStories.used_for==STORY4EVENT)
        num_stories_to_fix = db(q).count()
        comment(f"Start fixing refs. {num_stories_to_fix} remaining.")
        lst = db(q).select(limitby=(0, 100))
        pat_str = r'<a href="http://givat-brenner\.co\.il.(\w+)\.asp\?(\w+)=(\d+).*?>'  #should work, but it doesn't. hence next line
        pat_str = r'<a href.*?givat-brenner\.co\.il.(\w+)\.asp\?(\w+)=(\d+).*?>'
        pat = re.compile(pat_str, re.IGNORECASE)
        num_modified = 0
        num_failed = 0
        num_non_refs = 0
        for rec in lst:
            self.curr_story_id = rec.id
            comment(f"fixing story {rec.id}")
            txt = rec.story
            m = pat.search(txt)
            if m:
                ne = self.num_errors
                new_txt = pat.sub(self.replace_ref, txt)
                if self.num_errors > ne:
                    num_failed += 1
                else:
                    rec.update_record(story=new_txt)
                    num_modified += 1
            else:
                num_non_refs += 1
                comment(f"not a real ref in story {self.curr_story_id}")
        num_stories_to_fix = db(q).count()
        for what in self.counter:
            n = self.counter[what]
            comment(f'{n} refs of type {what}')
        return num_modified, num_failed, num_non_refs, num_stories_to_fix
    
def recover_uploaded_photo_dates():
    src_folder = local_photos_folder(SQUARES)
    nh = len(src_folder)
    src_folder += 'uploads/'
    cnt = 0
    for (root, dirnames, filenames) in os.walk(src_folder):
        for filename in filenames:
            path = root + '/' + filename
            photo_path = path[nh:]
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(path)
            upload_date = datetime.datetime.fromtimestamp(mtime)
            rec = db(db.TblPhotos.photo_path==photo_path).select().first()
            if rec:
                if rec.upload_date == None or rec.upload_date == NO_DATE:
                    uploader = rec.uploader or 6 #Itai Tadmor uploaded most of them
                    rec.update(upload_date=upload_date, uploader=uploader)
                    cnt += 1
    return "{} photo dates recovered".format(cnt)
        
def fix_old_site_refs():
    fixer = RefsFixer()
    num_modified, num_failed, num_non_refs, num_stories_to_fix = fixer.fix_old_site_refs()
    return "{n} refs fixed. {nf} failed. {nnr} non links. {ne} errors occured. {nl} remaining unfixed.".format(n=num_modified, nf=num_failed, nnr=num_non_refs, ne=fixer.num_errors, nl=num_stories_to_fix)

def clean_all_style_defs():
    count = 0
    lst = db(db.TblStories).select()
    for rec in lst:
        orig_html = rec.story
        html = clean_html(orig_html)
        if orig_html != html:
            count += 1
            rec.update_record(story=html)
    return "style, font, lang, class, div and align removed from {} stories.".format(count)
        
def delete_detached_life_stories():
    lst = db(db.TblMembers.deleted==False).select(db.TblMembers.story_id)
    lst = [rec.story_id for rec in lst]
    lst = set(lst)
    lifes = db((db.TblStories.used_for==1)&(db.TblStories.deleted==False)).select(db.TblStories.id)
    lifes = [rec.id for rec in lifes]
    orphans = [i for i in lifes if i not in lst]
    deleted_orphans = db(db.TblStories.id.belongs(orphans)).update(deleted=True)
    return "{} detached life stories out of {} were marked as deleted. story ids: {}".format(deleted_orphans, len(orphans), orphans)

def upgrade_to_date_ranges():
    for tblName in ['TblPhotos', 'TblEvents', 'TblMembers']:
        tbl = db[tblName]
        for fld in tbl:
            if fld.type == 'date':
                fld_str_name = fld.name + '_str'
                if fld_str_name in tbl:
                    for rec in db(tbl).select():
                        fld_str = rec[fld_str_name] or '????-??-??'
                        year, month, day = fld_str.split('-')
                        if year == '????':
                            formattd_date = ""
                            span = 0
                            unit = 'N'
                        elif year[3] == '?':
                            formatted_date = year[:3] + '0'
                            span = 10
                            unit = 'Y'
                        elif month == '??':
                            formatted_date = year
                            span = 0
                            unit = 'Y'
                        elif day == '??':
                            formatted_date = month + '/' + year
                            span = 0
                            unit = 'M'
                        else:
                            formatted_date = day + '/' + month + '/' + year
                            span = 0
                            unit = 'D'
                        data = dict()
                        data[fld.name + '_dateunit'] = unit
                        data[fld.name + '_datespan'] = span
                        rec.update_record(**data)
    return 'date ranges were upgraded'

def port_hit_counts():
    db.TblPageHits.insert(what='APP', item_id=0, count=0)
    for member in db(db.TblMembers.deleted!=True).select():
        if member.PageHits:
            db.TblPageHits.insert(what='MEMBER', item_id=member.id, count=member.PageHits)
    
    for event in db(db.TblEvents).select():
        if event.PageHits:
            db.TblPageHits.insert(what='EVENT', item_id=event.id, count=event.PageHits)
            
    for term in db(db.TblTerms).select():
        if term.PageHits:
            db.TblPageHits.insert(what='TERM', item_id=term.id, count=term.PageHits)
    
    for photo in db(db.TblPhotos).select():
        if photo.PageHits:
            db.TblPageHits.insert(what='PHOTO', item_id=photo.id, count=photo.PageHits)
        
    return "Hit counts were ported"

def approve_all_members():
    for member in db(db.TblMembers.deleted!=True).select():
        member.update_record(approved=True)
    return "All members are now approved"

def create_stories_for_all_photos():
    sm = Stories()
    lst = db(db.TblPhotos.story_id==None).select()
    for i, r in enumerate(lst):
        story_info = sm.get_empty_story(used_for=STORY4PHOTO, story_text="", name=r.Name)
        result = sm.add_story(story_info)
        r.update_record(story_id=result.story_id)
        if i % 100 == 0:
            db.commit()
    return "All photos have stories now"

def populate_empty_names():
    for member_rec in db(db.TblMembers.Name==None).select():
        member_rec.update_record(Name="")    
    for member_rec in db(db.TblMembers.Name=="").select():
        member_rec.update_record(Name=member_rec.first_name + ' ' + member_rec.last_name)
    for event_rec in db(db.TblEvents.Name=="").select():
        story = db(db.TblStories.id==event_rec.story_id).select(db.TblStories.name).first()
        event_rec.update_record(Name=story.name)
    return "Empty names were populated"

def delete_obsolete_words():
    lst = db(db.TblWords).select()
    num_deleted = 0
    for i, wr in enumerate(lst):
        cnt = db(db.TblWordStories.word_id==wr.id).count()
        if not cnt:
            db(db.TblWords.id==wr.id).delete()
            num_deleted += 1
        if (i % 100) == 0:
            db.commit()
    return '{} obsolete words were deleted'.format(num_deleted)
    
def calc_photos_usage():
    for p in db((db.TblPhotos.deleted!=True)&(db.TblPhotos.usage==None)).select():
        p.update_record(usage=0)
    n = 0
    lst = db(db.TblMemberPhotos).select(db.TblMemberPhotos.Photo_id, db.TblMemberPhotos.Photo_id.count(), groupby=[db.TblMemberPhotos.Photo_id])
    for mp in lst:
        if mp._extra['COUNT(TblMemberPhotos.Photo_id)'] > 0:
            db(db.TblPhotos.id==mp.TblMemberPhotos.Photo_id).update(usage = 1)
            n += 1
    lst = db(db.TblItemTopics.item_type=='P').select(db.TblItemTopics.item_id, db.TblItemTopics.item_id.count(), groupby=[db.TblItemTopics.item_id])
    for tp in lst:
        pr = db(db.TblPhotos.id==tp.TblItemTopics.item_id).select().first()
        x = tp._extra['COUNT(TblItemTopics.item_id)']
        if pr.usage == 0:
            n += 1
            pr.update_record(usage = pr.usage + 2)
    unused = db(db.TblPhotos.usage==0).count()
    return "{} photos were marked as relevant, {} are not.".format(n, unused)

def init_story_versions():
    n = db(db.TblStories.deleted!=True).update(last_version=0, approved_version=0)
    lst = db(db.TblStoryVersions).select(db.TblStoryVersions.story_id, db.TblStoryVersions.story_id.count(), groupby=[db.TblStoryVersions.story_id])
    for sv in lst:
        story_rec = db(db.TblStories.id==sv.TblStoryVersions.story_id).select().first()
        cnt = sv._extra['COUNT(TblStoryVersions.story_id)']
        story_rec.update(last_version=cnt, approved_version=cnt)
    return '{} story versions were initialized'.format(len(lst))
    
def init_database():
    return "database initialized"
