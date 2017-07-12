
# -*- coding: utf-8 -*-

from porting.create_old_db_mappings import table_fields, csv_name_to_table_name, get_records, csv_name_to_table_name
from glob import glob
import re
from photos import scan_all_unscanned_photos, fit_all_sizes
import random

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

    lst = db(db.TblPhotos.Description != '').select(db.TblPhotos.Description, db.TblPhotos.id)
    for rec in lst:
        story_id = db.TblStories.insert(story=rec.Description, used_for=STORY4PHOTO)
        db(db.TblPhotos.id==rec.id).update(story_id=story_id, Description='', DescriptionNoHtml='')

    lst = db(db.TblTerms.Background != '').select(db.TblTerms.Background, db.TblTerms.id)
    for rec in lst:
        story_id = db.TblStories.insert(story=rec.Background, used_for=STORY4EVENT)
        db(db.TblTerms.id==rec.id).update(story_id=story_id, Background='', BackgroundNoHtml='')

    return 'Finished consolidation of stories'

def is_hebrew(s):
    alef = 'א'
    tav = 'ת'
    alef = alef.decode('utf8')
    tav = tav.decode('utf8')
    for c in s:
        if c < alef or c > tav:
            return False
    return True

def name_stories():
    lst = db(db.TblStories).select()
    for i, rec in enumerate(lst):
        story = rec.story.decode('utf8')
        words = story[:300].split()
        words = [w for w in words if is_hebrew(w)]
        name = ' '.join(words[:5])
        db(db.TblStories.id==rec.id).update(name=name)
    return 'Finished naming stories'

def fix_photo_location_case():
    idx = dict()
    n_missing = 0
    n_fixed = 0
    with open('applications/' + request.application + '/static/gb_photos/tmp.lst') as f:
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

def scan_photos():
    return scan_all_unscanned_photos()

def collect_photographers():
    db.TblPhotographers.truncate('RESTART IDENTITY CASCADE')
    lst = db(db.TblPhotos.width>0).select()
    for rec in lst:
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
    lst = db(db.TblPhotos.width>0).select()
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
    year = 1800
    raw_str = '1800'
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
                raw_str = str(year) + '-'
        else:
            m = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', s)
            if m:
                day, mon, year = m.groups()
                day, mon, year = (int(day), int(mon), int(year))
                raw_str = s
            else:
                m = re.search(r'(\d{1,2})[./](\d{4})', s)
                if m:
                    mon, year = m.groups()
                    mon, year = (int(mon), int(year))
                    raw_str = s
                else:
                    m = re.search(r'(\d{4})', s)
                    if m:
                        year = int(m.groups()[0])
                        raw_str = s
  
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
                    data[k + '_str'] = val1
                    k1 = k.replace('birth', 'death')
                    data[k1] = datetime.datetime(day=1, month=1, year=int(val2))
                    data[k1 + '_str'] = val2
            rec.update_record(**data)
    return 'port_all_dates done!'
     
def port_photos_date():
    lst = db((db.TblPhotos.width>0) & (db.TblPhotos.photo_date==None)).select(db.TblPhotos.id, db.TblPhotos.PhotoDate, db.TblPhotos.photo_date, db.TblPhotos.photo_date_accuracy)
    for rec in lst:
        date, date_str = string_date_to_date(rec.PhotoDate)
        db(db.TblPhotos.id==rec.id).update(photo_date=date, photo_date_accuracy=accuracy)
    db.commit()

def port_topics():
    db.TblTopics.truncate('RESTART IDENTITY CASCADE')
    db.TblPhotoTopics.truncate()
    #collect keywords from photo list. later need to merge with event types...
    lst = db(db.TblPhotos.width>0).select()
    topic_collection = {}
    for rec in lst:
        s = rec.KeyWords
        if not s:
            continue
        topics = s.split(',')
        for topic in topics:
            topic = topic.strip()
            if topic in topic_collection:
                idx = topic_collection[topic]
            else:
                topic_collection[topic] = idx = db.TblTopics.insert(name=topic)
            db.TblPhotoTopics.insert(photo_id=rec.id, topic_id=idx)
    db.commit()
    
def create_random_photo_keys():
    for rec in db(db.TblPhotos).select():
        key = random.randint(1, 100)
        rec.update_record(random_photo_key=key)
    db.commit()
    
def fit_all_photo_sizes():
    fit_all_sizes()

def index():
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
        scan_photos()
        comment('start fixing photo location case')
        db.commit()
        collect_photographers()
        fix_photo_location_case()
        port_photos_date()
        port_topics()
        create_random_photo_keys()
        comment('Porting done')
    except Exception, e:
        log_exception('Porting old db failed')
    db.commit()
    return "Old db was converted and modified"

def rename_locations():
    for rec in db(db.TblPhotos).select():
        rec.update_record(photo_path="ported/" + rec.LocationInDisk)
    