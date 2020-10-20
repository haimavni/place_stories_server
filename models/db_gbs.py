import datetime
import random
from folders import local_folder, url_folder, safe_open
NO_DATE = datetime.date(day=1, month=1, year=1)
NO_TIME = datetime.datetime(day=1, month=1, year=1)
FAR_FUTURE = datetime.date(day=1, month=1, year=3000)
SAMPLING_SIZE = 10000

STORY4MEMBER = 1
STORY4EVENT = 2
STORY4PHOTO = 3
STORY4TERM = 4
STORY4MESSAGE = 5
STORY4HELP = 6
STORY4FEEDBACK = 7
STORY4VIDEO = 8
STORY4DOC = 9
STORY4AUDIO = 10
STORY4LETTER = 11
STORY4ARTICLE = 12
STORY4USER = [STORY4MEMBER, STORY4EVENT, STORY4PHOTO, STORY4TERM, STORY4VIDEO, STORY4DOC, STORY4AUDIO, STORY4ARTICLE] 

VIS_NEVER = 0           #for non existing members such as the child of a childless couple (it just connects them)
VIS_NOT_READY = 1
VIS_VISIBLE = 2
VIS_HIGH = 3            #

db.define_table('TblChatGroup',
                Field('name', type='string'),
                Field('key', type='string'),
                Field('moderator_id', type=db.auth_user),
                Field('story_id', type='integer'), 
                Field('public', type='boolean', default=True)
)

db.define_table('TblStories',
                Field('name', type='string'),
                Field('topic', type='string'),
                Field('story', type='text'),
                Field('preview', type='text'),
                Field('auto_preview', type='boolean', default=True),
                Field('creation_date', type='datetime'),
                Field('historic_date', type='string'), #for old stories
                Field('story_date', type='date', default=NO_DATE),
                Field('story_date_dateunit', type='string', default='Y'), # D, M or Y for day, month, year
                Field('story_date_datespan', type='integer', default=1), # how many months or years in the range
                Field('story_date_dateend', type='date', default=NO_DATE),
                Field('last_update_date', type='datetime'),
                Field('source', type='string'),
                Field('author_id', type=db.auth_user),
                Field('updater_id', type=db.auth_user),
                Field('indexing_date', type='datetime', default=NO_DATE),
                Field('used_for', type='integer'),  #member, event, photo, term, message
                Field('keywords', type='string'),  #to be calculated automatically using tfidf
                Field('story_len', type='integer', compute=lambda row: len(row.story)),
                Field('is_tagged', type='boolean', default=False),
                Field('language', type='string'),
                Field('translated_from', type='integer'), ##db.TblStories 
                Field('deleted', type='boolean', default=False),
                Field('dead', type='boolean', default=False), #can not be undeleted
                Field('visibility', type='integer', default=SV_PUBLIC),
                Field('touch_time', type='date', default=NO_DATE), #used to promote stories
                Field('last_version', type='integer'),
                Field('approved_version', type='integer'),
                Field('sampling_id', type='integer', default=random.randint(1, SAMPLING_SIZE)),
                Field('chatroom_id', type='integer'), # actually db.TblChatGroup),but then deletion of the chatroom deletes the story!
                Field('last_chat_time', type='datetime', default=NO_DATE),
                Field('sorting_key', type='string', default=''), # sequence of zero-padded integers
                Field('book_id', type='integer'),
                Field('imported_from', type='string')
)                

db.define_table('TblStoryVersions',
                Field('story_id', type=db.TblStories),
                Field('version_num', type='integer'),
                Field('creation_date', type='datetime'),
                Field('author_id', type=db.auth_user),
                Field('delta', type='text'),
                Field('language', type='string')
)

db.define_table('TblWords',
                Field('word', type='string'),
                Field('click_count', type='integer', default=0)
)

db.define_table('TblWordStories',
                Field('word_id', type=db.TblWords),
                Field('story_id', type=db.TblStories),
                Field('word_count', type='integer')
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
                Field('Event_id', type='integer'),
                Field('Member_id', type='integer'),
)

db.define_table('TblEventArticles',
                Field('event_id', type='integer'),
                Field('article_id', type='integer'),
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
                Field('event_date', type='date', default=NO_DATE),
                Field('event_date_dateunit', type='string', default='Y'),
                Field('event_date_datespan', type='integer', default=1),
                Field('event_date_dateend', type='date', default=NO_DATE),
                Field('EventRank', type='integer'),
                Field('IIDD', type='integer'),
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
                Field('deleted', type='boolean', default=False)
)

db.define_table('TblTermMembers',
                Field('term_id', type='integer'),
                Field('Member_id', type='integer'),
)

db.define_table('TblTermArticles',
                Field('term_id', type='integer'),
                Field('article_id', type='integer'),
)

db.define_table('TblTermPhotos',
                Field('term_id', type='integer'),
                Field('Photo_id', type='integer'),
)

db.define_table('TblFamilyConnectionTypes',
                Field('Description', type='string'),
                Field('IIDD', type='integer'),
)

db.define_table('TblMemberPhotos',
                Field('MemberID', type='integer'),
                Field('Member_id', type='integer'),
                Field('PhotoID', type='integer'),
                Field('Photo_id', type='integer'),
                Field('x', type='integer'),   #location of face in the picture
                Field('y', type='integer'),
                Field('r', type='integer'),
                Field('who_identified', type=db.auth_user)
)

db.define_table('TblArticlePhotos',
                Field('article_id', type='integer'),
                Field('photo_id', type='integer'),
                Field('x', type='integer'),   #location of face in the picture
                Field('y', type='integer'),
                Field('r', type='integer'),
                Field('who_identified', type=db.auth_user)
)

db.define_table('TblMembers',
                Field('title', type='string'),
                Field('first_name', type='string'),
                Field('last_name', type='string'),
                Field.Virtual('full_name', lambda rec: (rec.title + ' ' if rec.title else '') + rec.first_name + ' ' + rec.last_name),
                Field('former_first_name', type='string'),
                Field('former_last_name', type='string'),
                Field('DateOfAlia', type='string'),
                Field('date_of_alia', type='date', default=NO_DATE),
                Field('date_of_alia_dateunit', type='string', default='N'),
                Field('date_of_alia_datespan', type='integer', default=0),
                Field('date_of_alia_dateend', type='date', default=NO_DATE),
                Field('DateOfBirth', type='string'),
                Field('date_of_birth', type='date', default=NO_DATE), 
                Field('date_of_birth_dateunit', type='string', default='N'), 
                Field('date_of_birth_datespan', type='integer', default=0), 
                Field('date_of_birth_dateend', type='date', default=NO_DATE),
                Field('date_of_death', type='date', default=NO_DATE),
                Field('date_of_death_dateunit', type='string', default='N'),
                Field('date_of_death_datespan', type='integer', default=0),
                Field('date_of_death_dateend', type='date', default=NO_DATE),
                Field('cause_of_death', type='integer', default=0),
                Field('DateOfMember', type='string'),
                Field('date_of_member', type='date', default=NO_DATE),
                Field('date_of_member_dateunit', type='string', default='N'),
                Field('date_of_member_datespan', type='integer', default=0),
                Field('date_of_member_dateend', type='date', default=NO_DATE),
                Field('Education', type='string'),
                Field('FormerName', type='string'),
                Field('gender', type='string'), #F, M and also FM and MF for transgenders...
                Field('IIDD', type='integer'),
                Field('father_id', type='integer'), #all family relations can be derived from these 2 fields.
                Field('mother_id', type='integer'), #virtual child can define childless married couple etc. 
                Field('member_photo_id', type='integer'),
                Field('visible', type='boolean'), #obsolete
                Field('visibility', type='integer'),
                Field('Institute', type='string'),
                Field('LifeStory', type='text'),
                Field('LifeStoryNoHtml', type='text'),
                Field('story_id', type=db.TblStories),
                Field('Name', type='string'),
                Field('NickName', type='string'),
                Field('ObjectID', type='integer'),
                Field('Object_id', type='integer'),
                Field('PageHits', type='integer'),
                Field('PlaceOfBirth', type='string'),
                Field('place_of_death', type='string', default=""),
                Field('Professions', type='string'),
                Field('StatusID', type='integer'),
                Field('Status_id', type='integer'),
                Field('facePhotoURL', type='string'),
                Field('facePhotoURL_webp', type='string'),
                Field('deleted', type='boolean', default=False),
                Field('update_time', type='datetime'),
                Field('updater_id', type=db.auth_user),
                Field('divorced_parents', type='boolean', default=False),  #do not show parents as couple
                Field('approved', type='boolean')
)

db.define_table('TblArticles',
                Field('name', type='string'),
                Field('date_start', type='date', default=NO_DATE),
                Field('date_start_dateunit', type='string', default='N'),
                Field('date_start_datespan', type='integer', default=0),
                Field('date_start_dateend', type='date', default=NO_DATE),
                Field('date_end', type='date', default=NO_DATE),
                Field('date_end_dateunit', type='string', default='N'),
                Field('date_end_datespan', type='integer', default=0),
                Field('date_end_dateend', type='date', default=NO_DATE),
                Field('story_id', type=db.TblStories),
                Field('deleted', type='boolean', default=False),
                Field('facePhotoURL', type='string'),
                Field('facePhotoURL_webp', type='string'),
                Field('update_time', type='datetime'),
                Field('updater_id', type=db.auth_user),
)

db.define_table('TblPhotographers',
                Field('name', type='string'),
                Field('kind', type='string') #P=photograps, V=video, PV=both
)

db.define_table('TblRecorders',  #audio authors
                Field('name', type='string')
)

db.define_table('TblChats',
                Field('chat_group', type=db.TblChatGroup),
                Field('author', type=db.auth_user),
                Field('timestamp', type='datetime'),
                Field('message', type='text')
)

db.define_table('TblPhotos',
                Field('ArchiveNum', type='string'),
                Field('Description', type='text'),
                Field('DescriptionNoHtml', type='text'),
                Field('story_id', type=db.TblStories),
                Field('IIDD', type='integer'),
                Field('LocationInDisk', type='string'),
                Field('photo_path', type='string'),
                Field('webp_photo_path', type='string'),
                Field('Name', type='string'),
                Field('original_file_name', type='string'),
                Field('embedded_photo_date', type='datetime'),
                Field('ObjectID', type='integer'), #obsolete, to be replaced by the following line
                Field('Object_id', type='integer'),
                Field('PageHits', type='integer'),
                Field('PhotoDate', type='string'),
                Field('photo_date', type='date', default=NO_DATE),
                Field('photo_date_dateunit', type='string', default='Y'), # D, M or Y for day, month, year
                Field('photo_date_datespan', type='integer', default=1), # how many months or years in the range
                Field('photo_date_dateend', type='date', default=NO_DATE),
                Field('latitude', type='float'),
                Field('longitude', type='float'),
                Field('zoom', type='integer', default=12),
                Field('PhotoRank', type='integer'),
                Field('Photographer', type='string'), #obsolete
                Field('photographer_id', type='integer'),
                Field('Recognized', type='boolean'),
                Field('StatusID', type='integer'),
                Field('Status_id', type='integer'),
                Field('width', type='integer', default=0),
                Field('height', type='integer', default=0),
                Field('uploader', type=db.auth_user),
                Field('upload_date', type='datetime'),
                Field('last_mod_time', type='datetime'),
                Field.Virtual('stamped_photo_path', lambda rec: rec.photo_path + str(rec.last_mod_time)[:19] if rec.last_mod_time else ''),
                Field('photo_missing', type='boolean', default=False),
                Field('oversize', type='boolean', default=False), #If people want to download the full size they use this info
                Field('random_photo_key', type='integer'),
                Field('deleted', type='boolean', default=False),
                Field('is_back_side', type='boolean', default=False),
                Field('crc', type='integer'),
                Field('dhash', type='string'),
                Field('curr_dhash', type='string'),  #after editing such as rotation and cropping. will be used to reload photo after using photoshop etc.
                Field('dup_checked', type='boolean'),  #to be used only once, to detect all old dups. 
                Field('usage', type='integer', default=0) #1=has identified members 2=has assigned tags 3=both, #todo need to populate, then use
                #to select only relevant photos for opening slide show
)

db.define_table('TblPhotoPairs',
                Field('front_id', db.TblPhotos),
                Field('back_id', db.TblPhotos)
)

db.define_table('TblTopics',
                Field('name', type='string'),
                Field('description', type='string'),
                Field('topic_kind', type='integer', default=0), # 0=virgin, 1=group of topics 2=simple topic
                Field('usage', type='string') ## made of the letters EMPTVD for events, members, photos, terms, and videos
)

db.define_table('TblTopicGroups',
                Field('parent', type=db.TblTopics),
                Field('child', type=db.TblTopics)
)

db.define_table('TblItemTopics',
          Field('item_type', type='string', requires=IS_LENGTH(1)),  #M=Member, P=Photo, E=Event
          Field('topic_id', type=db.TblTopics),
          Field('story_id', type=db.TblStories)
)

db.define_table('TblVideos',
                Field('name', type='string'),
                Field('video_type', type='string'),
                Field('src', type='string'),
                Field('deleted', type='boolean', default=False),
                Field('photographer_id', type='integer'),
                Field('story_id', type=db.TblStories),
                Field('contributor', type=db.auth_user),
                Field('video_date', type='date', default=NO_DATE),
                Field('video_date_dateunit', type='string', default='Y'), # D, M or Y for day, month, year
                Field('video_date_datespan', type='integer', default=1), # how many months or years in the range
                Field('video_date_dateend', type='date', default=NO_DATE),
                Field('touch_time', type='date', default=NO_DATE), #used to promote videos
                Field('upload_date', type='datetime')
                )

db.define_table('TblDocs',
                Field('name', type='string'),
                Field('doc_type', type='string'),
                Field('deleted', type='boolean', default=False),
                Field('story_id', type=db.TblStories),
                Field('text_extracted', type='boolean', default=False),
                Field('uploader', type=db.auth_user),
                Field('doc_date', type='date', default=NO_DATE),
                Field('doc_date_dateunit', type='string', default='Y'), # D, M or Y for day, month, year
                Field('doc_date_datespan', type='integer', default=1), # how many months or years in the range
                Field('doc_date_dateend', type='date', default=NO_DATE),
                Field('touch_time', type='date', default=NO_DATE), #used to promote docs
                Field('doc_path', type='string'),
                Field('original_file_name', type='string'),
                Field('crc', type='integer'),
                Field('upload_date', type='datetime')
                )

db.define_table('TblAudios',
                Field('name', type='string'),
                Field('audio_type', type='string'),
                Field('deleted', type='boolean', default=False),
                Field('story_id', type=db.TblStories),
                Field('uploader', type=db.auth_user),
                Field('audio_date', type='date', default=NO_DATE),
                Field('audio_date_dateunit', type='string', default='Y'), # D, M or Y for day, month, year
                Field('audio_date_datespan', type='integer', default=1), # how many months or years in the range
                Field('audio_date_dateend', type='date', default=NO_DATE),
                Field('touch_time', type='date', default=NO_DATE), #used to promote docs
                Field('audio_path', type='string'),
                Field('original_file_name', type='string'),
                Field('crc', type='integer'),
                Field('upload_date', type='datetime'),
                Field('recorder_id', type=db.TblRecorders)
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
                Field('deleted', type='boolean', default=False)
)

db.define_table('TblPageHits',
                Field('what', type='string'),
                Field('item_id', type='integer'),
                Field('count', type='integer', default=0),
                Field('new_count', type='integer', default=0)
                )

db.define_table('TblFeedback',
                Field('fb_code_version', type='string'), 
                Field('fb_bad_message', type='text'),
                Field('fb_good_message', type='text'),
                Field('fb_email', type='string'),
                Field('fb_name', type='string'),
                Field('fb_device_type', type='string'),
                Field('fb_device_details', type='string')
                )

db.define_table('TblConfiguration',
                Field('languages', type='string', default='he,en'),
                Field('description', type='string'),
                Field('fix_level', type='integer', default=0),
                Field('enable_auto_registration', type='boolean', default=False),
                Field('initial_privileges', type='string', default='EDITOR;PHOTO_UPLOADER;CHATTER'),
                Field('expiration_date', type='date'),
                Field('expose_new_app_button', type='boolean', default=True),
                Field('expose_feedback_button', type='boolean', default=True),
                Field('quick_upload_button', type='boolean', default=False),
                Field('expose_version_time', type='boolean', default=True),
                Field('expose_developer', type='boolean', default=True),
                Field('support_audio', type='boolean', default=False),
                Field('help_messages_upload_time', type='datetime', default=NO_DATE),
                Field('letter_templates_upload_time', type='datetime', default=NO_DATE),
                Field('enable_articles', type='boolean', default=False),
                Field('enable_member_of_the_day', type='boolean', default=True),
                Field('enable_books', type='boolean', default=True),
                Field('promoted_story_expiration', type='integer', default=7)
                )

db.define_table('TblLocaleCustomizations',
                Field('lang', type='string'),
                Field('key', type='string'),
                Field('value', type='string')
                )

db.define_table('TblCustomers',
                Field('first_name', type='string'),
                Field('last_name', type='string'),
                Field('email', type='string'),
                Field('password', type='string'),
                Field('host', type='string', default=request.env.http_host.split(':')[0]),
                Field('app_name', type='string'),
                Field('confirmation_key', type='string'),
                Field('created', type='boolean', default=False),
                Field('locale', type='string'),
                Field('creation_time', type='datetime', default=request.now)
                )

db.define_table('TblMenus',
                Field('name', type='string')
                )

db.define_table('TblQuestions',
                Field('menu_id', type=db.TblMenus),
                Field('prompt', type='string'),
                Field('description', type='string')
                )

db.define_table('TblAnswers',
                Field('question_id', type=db.TblQuestions),
                Field('text', type='string'),
                Field('description', type='string')
                )

db.define_table('TblItemAnswers',
                Field('answer_id', type=db.TblAnswers),
                Field('item_id', type='integer') #ensure only one answer per question
                )

db.define_table('TblGroups',
                Field('description', type='string'),
                Field('logo_name', type='string'),
                Field('topic_id', type='integer'),
                Field('deleted', type='boolean', default=False) #todo: currently not used
                )

db.define_table('TblGroupContacts',
                Field('email', type='string'),
                Field('first_name', type='string'),
                Field('last_name', type='string'),
                Field('group_id', type=db.TblGroups),
                Field('deleted', type='boolean', default=False)
                )

db.define_table('TblShortcuts',
                Field('url', type='text'),
                Field('key', type='string')
                )

db.define_table('TblAuthorRights',
                Field('text', type='string')
                )

db.define_table('TblNotifications',
                Field('notification_text', type='string')
                )

db.define_table('TblNotified',
                Field('notified', type=db.auth_user),
                Field('notification', type=db.TblNotifications)
                )

db.define_table('TblBooks',
                Field('name', type='string'),
                Field('description', type='string')
                )

db.define_table('TblPinned',
                Field('story_id', type=db.TblStories)
                )

db.define_table('TblSearches',
                Field('pattern', type='string'),
                Field('count', type='integer')
                )

def write_indexing_sql_scripts():
    '''Creates a set of indexes if they do not exist.
       In a terminal, su postgres and issue the command
       psql -f create_indexes.sql <database-name>
    '''
    indexes = [
        ('TblMemberPhotos', 'Member_id'),
        ('TblMemberPhotos', 'Photo_id', 'x', 'y'),
        ('TblEventMembers', 'Member_id'),
        ('TblEventMembers', 'Event_id'),
        ('TblWordStories',  'word_id'),
        ('TblPhotos',       'crc')
    ]

    path = local_folder('logs')
    fname = path + 'indexes_created[{a}].txt'.format(a=request.application)
    if os.path.exists(fname):
        return
    with safe_open(fname, 'w') as f:
        f.write('Indexes create/drop sql scripts already created.\nDo not delete this file.')
    with safe_open(path + 'create_indexes[{a}].sql'.format(a=request.application), mode='w') as f:
        with safe_open(path + 'delete_indexes[{a}].sql'.format(a=request.application), mode='w') as g:
            for tcc in indexes:
                table = tcc[0]
                fields = ', '.join(tcc[1:])
                index_name = '_'.join(tcc) + '_idx'
                create_cmd = 'CREATE INDEX CONCURRENTLY {i} ON {t} ({f});'.format(i=index_name, t=table, f=fields)
                drop_cmd = 'DROP INDEX {};'.format(tcc[0])
                f.write(create_cmd + '\n')
                g.write(drop_cmd + '\n')

write_indexing_sql_scripts()                

translatable_fields = dict(
    TblEvents = ['Description', 'Name', 'Keyword', 'Place', 'SSource'],
    TblMembers = ['first_name', 'last_name', 'former_first_name', 'former_last_name', 'NickName'],
    TblPhotographers = ['name'],
    TblPhotos = ['Description', 'Name'],
    TblTopics = ['name', 'description'],
    TblVideos = ['name'],
    TblTerms = ['name']
)
