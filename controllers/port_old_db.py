
# -*- coding: utf-8 -*-

from porting.create_old_db_mappings import table_fields, csv_name_to_table_name, get_records, csv_name_to_table_name
from glob import glob
import re
from photos import scan_all_unscanned_photos

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
    lst = db(db.TblPhotos.width>0).select()
    for rec in lst:
        if not rec.Photographer:
            continue
        p = db(db.TblPhotographers.name==rec.Photographer).select().first()
        if p:
            i = p.id
        else:
            i = db.TblPhotographers.insert(name=rec.Photographer)
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
    if s:
        if p in s:
            m = re.search(r'(\d{1,2})', s)
            if m:
                y = m.groups()[0]
                if len(y) < 2:
                    y += '0'
                y = 1900 + int(y)
                accuracy = 'C' #decade
            else:
                y = 1928
                accuracy = 'X'
        else:
            m = re.search(r'(\d{4})', s)
            if m:
                y = int(m.groups()[0])
                accuracy = 'Y'
            else:
                y = 1928
                accuracy = 'X'
    else:
        y = 1928 #just to have someting there for sorting to kind of work
        accuracy = 'X' # fabricated date
    return (datetime.date(year=y, month=1, day=1), accuracy)
 
def port_photos_date():
    lst = db((db.TblPhotos.width>0) & (db.TblPhotos.photo_date==None)).select(db.TblPhotos.id, db.TblPhotos.PhotoDate, db.TblPhotos.photo_date, db.TblPhotos.photo_date_accuracy)
    for rec in lst:
        date, accuracy = string_date_to_date(rec.PhotoDate)
        db(db.TblPhotos.id==rec.id).update(photo_date=date, photo_date_accuracy=accuracy)
    db.commit()

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
        fix_photo_location_case()
        comment('Porting done')
    except Exception, e:
        log_exception('Porting old db failed')
    db.commit()
    return "Old db was converted and modified"