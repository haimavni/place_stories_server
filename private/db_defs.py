db.define_table('TblDefaults',
                Field('AdminHrefInitialAddress', type='string'),
                Field('AdminMaxResultsInPage', type='integer'),
                Field('AdminThumbnailPhotoHeight', type='integer'),
                Field('CommentsEmailAddress', type='string'),
                Field('CommentsEmailName', type='string'),
                Field('ID', type='integer'),
                Field('IdentifyEmailAddress', type='string'),
                Field('IdentifyEmailName', type='string'),
                Field('MailFromAddress', type='string'),
                Field('MailFromName', type='string'),
                Field('MailHost', type='string'),
                Field('MailPort', type='integer'),
                Field('NormalPhotoWidth', type='integer'),
                Field('PageHitsCountingStatus', type='integer'),
                Field('PhotosInEvent', type='integer'),
                Field('PhotosInMember', type='integer'),
                Field('ThumbnailPhotoWidth', type='integer'),
                Field('UserMaxPhotosInUnidentifiedPage', type='integer'),
                Field('UserMaxRandomEventsInMainPage', type='integer'),
                Field('UserMaxResultsInPage', type='integer'),
)

db.define_table('TblEventMembers',
                Field('EventID', type='integer'),
                Field('EventMemberRank', type='integer'),
                Field('MemberID', type='integer'),
)

db.define_table('TblEventPhotos',
                Field('EventID', type='integer'),
                Field('EventPhotoRank', type='integer'),
                Field('PhotoID', type='integer'),
)

db.define_table('TblEventTypes',
                Field('Description', type='string'),
                Field('ID', type='integer'),
                Field('ImageName', type='string'),
                Field('Name', type='string'),
)

db.define_table('TblEvents',
                Field('Description', type='string'),
                Field('DescriptionNoHtml', type='string'),
                Field('EventDate', type='string'),
                Field('EventRank', type='integer'),
                Field('ID', type='integer'),
                Field('KeyWords', type='string'),
                Field('Name', type='string'),
                Field('ObjectID', type='integer'),
                Field('PageHits', type='integer'),
                Field('Place', type='string'),
                Field('Source', type='string'),
                Field('StatusID', type='integer'),
                Field('TypeID', type='integer'),
)

db.define_table('TblFamilyConnectionTypes',
                Field('Description', type='string'),
                Field('ID', type='integer'),
)

db.define_table('TblHrefCategoryHrefs',
                Field('CategoryID', type='string'),
                Field('HrefID', type='integer'),
)

db.define_table('TblHrefTypes',
                Field('ID', type='integer'),
                Field('Name', type='string'),
)

db.define_table('TblMemberConnections',
                Field('ConnectToMemberID', type='integer'),
                Field('ConnectionTypeID', type='integer'),
                Field('DateOfBirth', type='string'),
                Field('ID', type='integer'),
                Field('MemberID', type='integer'),
                Field('Name', type='string'),
                Field('PlaceOfBirth', type='string'),
                Field('Professions', type='string'),
)

db.define_table('TblMemberPhotos',
                Field('MemberID', type='integer'),
                Field('MemberPhotoRank', type='integer'),
                Field('PhotoID', type='integer'),
)

db.define_table('TblMembers',
                Field('DateOfAlia', type='string'),
                Field('DateOfBirth', type='string'),
                Field('DateOfMember', type='string'),
                Field('Education', type='string'),
                Field('FormerName', type='string'),
                Field('ID', type='integer'),
                Field('Institute', type='string'),
                Field('KeyWords', type='string'),
                Field('LifeStory', type='text'),
                Field('LifeStoryNoHtml', type='text'),
                Field('Name', type='string'),
                Field('NickName', type='string'),
                Field('ObjectID', type='integer'),
                Field('PageHits', type='integer'),
                Field('PlaceOfBirth', type='string'),
                Field('Professions', type='string'),
                Field('StatusID', type='integer'),
)

db.define_table('TblObjects',
                Field('Description', type='string'),
                Field('HebrewDescription', type='string'),
                Field('ID', type='integer'),
                Field('Priority', type='integer'),
)

db.define_table('TblPhotos',
                Field('ArchiveNum', type='string'),
                Field('Description', type='string'),
                Field('DescriptionNoHtml', type='string'),
                Field('ID', type='integer'),
                Field('KeyWords', type='string'),
                Field('LocationInDisk', type='string'),
                Field('Name', type='string'),
                Field('ObjectID', type='integer'),
                Field('PageHits', type='integer'),
                Field('PhotoDate', type='string'),
                Field('PhotoRank', type='integer'),
                Field('Photographer', type='string'),
                Field('Recognized', type='integer'),
                Field('StatusID', type='integer'),
)

db.define_table('TblStatuses',
                Field('ID', type='integer'),
                Field('Name', type='string'),
)

db.define_table('TblSuperAdmins',
                Field('ID', type='integer'),
                Field('Name', type='string'),
                Field('Password', type='string'),
)

db.define_table('TblTerms',
                Field('Background', type='string'),
                Field('BackgroundNoHtml', type='string'),
                Field('ID', type='integer'),
                Field('InventedBy', type='string'),
                Field('InventedByMemberID', type='integer'),
                Field('Name', type='string'),
                Field('ObjectID', type='integer'),
                Field('PageHits', type='integer'),
                Field('StatusID', type='integer'),
                Field('TermTranslation', type='string'),
)


#mappings for conversion of old (ID) refs to native refs (id)

dblinks = dict(    
    TblEventMembers=[EventID, MemberID],
    TblEventPhotos=[EventID, PhotoID],
    TblEvents=[TypeID, ObjectID, StatusID],
    TblMemberConnections=[MemberID, ConnectToMemberID, ConnectionTypeID],
    TblMemberPhotos=[MemberID, PhotoID],
    TblMembers=[ObjectID, StatusID],
    TblPhotos=[ObjectID, StatusID],
    TblTerms=[InventedByMemberID, ObjectID, StatusID]
)    

map_dblink_to_table_name = dict(
    EventID='TblEvents',
    MemberID='TblMembers',
    PhotoID='TblPhotos',
    TypeID='TblEventTypes',
    ObjectID='TblObjects',
    StatusID='TblStatuses',
    ConnectToMemberID='Members',
    ConnectionTypeID='TblFamilyConnectionTypes',
    InventedByMemberID='TblMembers'
)

def convert_IDrefs():
    for tbl in dblinks:
        flds = dblinks[tbl]
        fields = [db[tbl][fld] for fld in flds]
        for rec in db(tbl).select(fields):
            for f in flds:
                new_fld = f[:-2] + '_id'
                ID = rec[f]
                if not ID:
                    continue
                other_table = map_dblink_to_table_name[f]
                other_field = other_table['ID']
                other_id_field = other_table['id']
                i = db(other_field==ID).select(other_id_field).first().id
                table = db[tbl]
                db(table.id==rec.id).update(new_fld=i)
            
