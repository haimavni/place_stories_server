from dal_utils import IS_FUZZY_DATE, represent_fuzzy_date

STORY4MEMBER = 1
STORY4EVENT = 2
STORY4PHOTO = 3
STORY4TERM = 4

T.force('he')

db.define_table('TblStories',
                Field('name', type='string'),
                Field('story', type='text'),
                Field('creation_date', type='datetime'),
                Field('author_id', type=db.auth_user),
                Field('used_for', type='integer'),  #member, event, photo, term
                Field('keywords', type='string')  #to be calculated automatically using tfidf
)

db.define_table('TblStoryVersions',
                Field('story_id', type=db.TblStories),
                Field('version_num', type='integer'),
                Field('creation_date', type='datetime'),
                Field('author_id', type=db.auth_user),
                Field('delta', type='text'),
)

db.define_table('TblDefaults',
                Field('AdminHrefInitialAddress', type='string'),
                Field('AdminMaxResultsInPage', type='integer'),
                Field('AdminThumbnailPhotoHeight', type='integer'),
                Field('CommentsEmailAddress', type='string'),
                Field('CommentsEmailName', type='string'),
                Field('IIDD', type='integer'),
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
                Field('Event_id', type='integer'),
                Field('EventMemberRank', type='integer'),
                Field('MemberID', type='integer'),
                Field('Member_id', type='integer'),
)

db.define_table('TblEventPhotos',
                Field('EventID', type='integer'),
                Field('Event_id', type='integer'),
                Field('EventPhotoRank', type='integer'),
                Field('PhotoID', type='integer'),
                Field('Photo_id', type='integer'),
)

db.define_table('TblEventTypes',
                Field('Description', type='string'),
                Field('IIDD', type='integer'),
                Field('ImageName', type='string'),
                Field('Name', type='string'),
)

db.define_table('TblEvents',
                Field('Description', type='text'),
                Field('DescriptionNoHtml', type='text'),
                Field('story_id', type=db.TblStories),
                Field('EventDate', type='string'),
                Field('EventRank', type='integer'),
                Field('IIDD', type='integer'),
                Field('KeyWords', type='string'),
                Field('Name', type='string'),
                Field('ObjectID', type='integer'),
                Field('Object_id', type='integer'),
                Field('PageHits', type='integer'),
                Field('Place', type='string'),
                Field('SSource', type='string'),
                Field('StatusID', type='integer'),
                Field('Status_id', type='integer'),
                Field('TypeID', type='integer'),
                Field('Type_id', type='integer'),
)

db.define_table('TblFamilyConnectionTypes',
                Field('Description', type='string'),
                Field('IIDD', type='integer'),
)

db.define_table('TblHrefCategoryHrefs',
                Field('CategoryID', type='string'),
                Field('Category_id', type='string'),
                Field('HrefID', type='integer'),
                Field('Href_id', type='integer'),
)

db.define_table('TblHrefTypes',
                Field('IIDD', type='integer'),
                Field('Name', type='string'),
)

db.define_table('TblMemberConnections',
                Field('ConnectToMemberID', type='integer'),
                Field('ConnectToMember_id', type='integer'),
                Field('ConnectionTypeID', type='integer'),
                Field('ConnectionType_id', type='integer'),
                Field('DateOfBirth', type='string'),
                Field('IIDD', type='integer'),
                Field('MemberID', type='integer'),
                Field('Member_id', type='integer'),
                Field('Name', type='string'),
                Field('PlaceOfBirth', type='string'),
                Field('Professions', type='string'),
)

db.define_table('TblMemberPhotos',
                Field('MemberID', type='integer'),
                Field('Member_id', type='integer'),
                Field('MemberPhotoRank', type='integer'),
                Field('PhotoID', type='integer'),
                Field('Photo_id', type='integer'),
                Field('x', type='integer'),   #location of face in the picture
                Field('y', type='integer'),
                Field('r', type='integer'),
)

db.define_table('TblMembers',
                Field('first_name', type='string'),
                Field('last_name', type='string'),
                Field('former_first_name', type='string'),
                Field('former_last_name', type='string'),
                Field('DateOfAlia', type='string'),
                Field('alia_date', type='date'),
                Field('alia_date_accuracy', type='string', length=1),  #D, M or Y - day, month or year
                Field('DateOfBirth', type='string'),
                Field('birth_date', type='date', 
                      requires=[IS_FUZZY_DATE()],
                      represent=lambda v: represent_fuzzy_date(v)
                      ),
                Field('date_of_death', type='date'),
                Field('date_of_death_accuracy', type='string', length=1),
                Field('DateOfMember', type='string'),
                Field('date_of_membership', type='date'),
                Field('date_of_membership_accuracy', type='string', length=1),
                Field('Education', type='string'),
                Field('FormerName', type='string'),
                Field('gender', type='string'), #F, M and also FM and MF for transgenders...
                Field('IIDD', type='integer'),
                Field('father_id', type='integer'), #all family relations can be derived from these 2 fields.
                Field('mother_id', type='integer'), #virtual child can define childless married couple etc. 
                Field('member_photo_id', type='integer'),
                Field('visible', type='boolean'),
                Field('Institute', type='string'),
                Field('KeyWords', type='string'),
                Field('LifeStory', type='text'),
                Field('LifeStoryNoHtml', type='text'),
                Field('story_id', type=db.TblStories),
                Field('Name', type='string'),
                Field('NickName', type='string'),
                Field('ObjectID', type='integer'),
                Field('Object_id', type='integer'),
                Field('PageHits', type='integer'),
                Field('PlaceOfBirth', type='string'),
                Field('Professions', type='string'),
                Field('StatusID', type='integer'),
                Field('Status_id', type='integer'),
)

db.define_table('TblObjects',
                Field('Description', type='string'),
                Field('HebrewDescription', type='string'),
                Field('IIDD', type='integer'),
                Field('Priority', type='integer'),
)

db.define_table('TblPhotos',
                Field('ArchiveNum', type='string'),
                Field('Description', type='text'),
                Field('DescriptionNoHtml', type='text'),
                Field('story_id', type=db.TblStories),
                Field('IIDD', type='integer'),
                Field('KeyWords', type='string'),
                Field('LocationInDisk', type='string'),
                Field('Name', type='string'),
                Field('ObjectID', type='integer'),
                Field('Object_id', type='integer'),
                Field('PageHits', type='integer'),
                Field('PhotoDate', type='string'),
                Field('PhotoRank', type='integer'),
                Field('Photographer', type='string'),
                Field('Recognized', type='boolean'),
                Field('StatusID', type='integer'),
                Field('Status_id', type='integer'),
                Field('width', type='integer', default=0),
                Field('height', type='integer', default=0),
                Field('uploader', type=db.auth_user),
                Field('upload_date', type='datetime'),
                Field('photo_missing', type='boolean')
)

db.define_table('TblStatuses',
                Field('IIDD', type='integer'),
                Field('Name', type='string'),
)

db.define_table('TblSuperAdmins',
                Field('IIDD', type='integer'),
                Field('Name', type='string'),
                Field('Password', type='string'),
)

db.define_table('TblTerms',
                Field('Background', type='text'),
                Field('BackgroundNoHtml', type='text'),
                Field('story_id', type=db.TblStories),
                Field('IIDD', type='integer'),
                Field('InventedBy', type='string'),
                Field('InventedByMemberID', type='integer'),
                Field('InventedByMember_id', type='integer'),
                Field('Name', type='string'),
                Field('ObjectID', type='integer'),
                Field('Object_id', type='integer'),
                Field('PageHits', type='integer'),
                Field('StatusID', type='integer'),
                Field('Status_id', type='integer'),
                Field('TermTranslation', type='string'),
)

db.define_table('TblChatGroup',
                Field('name', type='string'),
                Field('moderator_id', type=db.auth_user),
                Field('public', type='boolean', default=True)
)

db.define_table('TblChats',
                Field('chat_group', type=db.TblChatGroup),
                Field('author', type=db.auth_user),
                Field('timestamp', type='datetime'),
                Field('message', type='text')
)

def write_indexing_sql_scripts():
    '''Creates a set of indexes if they do not exist'''
    indexes = [
        ('TblMemberPhotos', 'Member_id'),
        ('TblMemberPhotos', 'Photo_id', 'x', 'y'),
        ('TblEventMembers', 'Member_id'),
        ('TblEventMembers', 'Event_id'),
    ]

    path = 'applications/' + request.application + '/logs/'
    fname = path + 'indexes_created.txt'
    if os.path.exists(fname):
        return
    with open(fname, 'w') as f:
        f.write('Indexes create/drop sql scripts already created.\nDo not delete this file.')
    with open(path + 'create_indexes.sql', mode='w') as f:
        with open(path + 'delete_indexes.sql', mode='w') as g:
            for tcc in indexes:
                table = tcc[0]
                fields = ', '.join(tcc[1:])
                index_name = '_'.join(tcc) + '_idx'
                create_cmd = 'CREATE INDEX CONCURRENTLY {i} ON {t} ({f});'.format(i=index_name, t=table, f=fields)
                drop_cmd = 'DROP INDEX {};'.format(tcc[0])
                f.write(create_cmd + '\n')
                g.write(drop_cmd + '\n')

write_indexing_sql_scripts()                

