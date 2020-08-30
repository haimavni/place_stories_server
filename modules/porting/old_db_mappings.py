def fields_template():

    alldefs = dict()
    dblink = 'integer'

    #alldefs["TblAdmins"] = dict(
        #IIDD='string',
        #Name='string',
        #Password='string',
    #)

    alldefs["TblDefaults"] = dict(
        IIDD='integer',
        AdminMaxResultsInPage='integer',
        UserMaxResultsInPage='integer',
        PhotosInMember='integer',
        PhotosInEvent='integer',
        NormalPhotoWidth='integer',
        ThumbnailPhotoWidth='integer',
        AdminThumbnailPhotoHeight='integer',
        UserMaxRandomEventsInMainPage='integer',
        PageHitsCountingStatus='integer',
        CommentsEmailName='string',
        CommentsEmailAddress='string',
        IdentifyEmailName='string',
        IdentifyEmailAddress='string',
        MailHost='string',
        MailPort='integer',
        MailFromAddress='string',
        MailFromName='string',
        UserMaxPhotosInUnidentifiedPage='integer',
        AdminHrefInitialAddress='string',
    )

    #alldefs["TblDocuments"] = dict(
        #IIDD='string',
        #ArchiveNum='string',
        #DocumentDate='string',
        #Description='string',
        #LocationInDisk='string',
        #StatusID='string',
    #)

    #alldefs["TblEventDocuments"] = dict(
        #EventID='string',
        #DocumentID='string',
        #EventDocumentRank='string',
    #)

    alldefs["TblEventMembers"] = dict(
        EventID=dblink,
        MemberID=dblink,
        EventMemberRank='integer',
    )

    alldefs["TblEventPhotos"] = dict(
        EventID=dblink,
        PhotoID=dblink,
        EventPhotoRank='integer',
    )

    alldefs["TblEventTypes"] = dict(
        IIDD=dblink,
        Name='string',
        Description='string',
        ImageName='string',
    )

    alldefs["TblEvents"] = dict(
        IIDD=dblink,
        Name='string',
        SSource='string',
        EventDate='string', #may be missing, just year, years range or true date
        Place='string',
        Description='string',
        KeyWords='string',
        EventRank='integer',
        TypeID=dblink, #db.TblEventTypes
        ObjectID=dblink, #db.TblObjects
        StatusID=dblink, #db.TblStatuses
        PageHits='integer',
        DescriptionNoHtml='string',
    )

    alldefs["TblFamilyConnectionTypes"] = dict(
        IIDD=dblink,
        Description='string',
    )

    #alldefs["TblHrefCategories"] = dict(
        #IIDD='string',
        #Name='string',
        #CategoryRank='string',
    #)

    #alldefs["TblHrefCategoryCategories"] = dict(
        #ChildCategoryID='string',
        #ParentCategoryID='string',
        #ChildHierarchyLevel='string',
    #)

    alldefs["TblHrefCategoryHrefs"] = dict(
        HrefID=dblink, #db.Tbl???
        CategoryID='string',
    )

    alldefs["TblHrefTypes"] = dict(
        IIDD=dblink,
        Name='string',
    )

    #alldefs["TblHrefs"] = dict(
        #IIDD='string',
        #Name='string',
        #Description='string',
        #Href='string',
        #HrefTypeID='string',
        #HrefRank='string',
        #DescriptionNoHtml='string',
    #)

    #alldefs["TblJokes"] = dict(
        #IIDD='string',
        #Description='string',
    #)

    alldefs["TblMemberConnections"] = dict(
        IIDD=dblink,
        MemberID=dblink, #db.TblMdembers
        ConnectToMemberID=dblink, #db.TblMdembers
        ConnectionTypeID=dblink, #db.TblFamilyConnectionTypes
        Name='string',
        DateOfBirth='string', #redundant
        PlaceOfBirth='string',
        Professions='string',
    )

    #alldefs["TblMemberDocuments"] = dict(
        #MemberID='string',
        #DocumentID='string',
        #MemberDocumentRank='string',
    #)

    alldefs["TblMemberPhotos"] = dict(
        MemberID=dblink, #db.TblMembers
        PhotoID=dblink, #db.TblMembers
        MemberPhotoRank='integer',
    )

    alldefs["TblMembers"] = dict(
        IIDD=dblink,
        Name='string',
        FormerName='string',
        DateOfBirth='string', #may be missing, year or range...
        PlaceOfBirth='string',
        DateOfAlia='string', #missing or year
        DateOfMember='string', #missing or year
        Education='string', #drop it
        Institute='string', #drop it
        Professions='string', #drop it
        LifeStory='text',
        KeyWords='string',
        ObjectID=dblink, #db.TblObjects. probably reduntdant
        NickName='string',
        StatusID=dblink, #db.TblStatuses
        PageHits='integer',
        LifeStoryNoHtml='text',
    )

    alldefs["TblObjects"] = dict(
        IIDD=dblink,
        Description='string',
        Priority='integer',
        HebrewDescription='string',
    )

    alldefs["TblPhotos"] = dict(
        IIDD=dblink,
        ArchiveNum='string',
        PhotoDate='string', #range, year, etc.
        Name='string',
        Description='string',
        Photographer='string',
        KeyWords='string',
        LocationInDisk='string',
        PhotoRank='integer',
        ObjectID=dblink, #db.TblObjects
        Recognized='boolean',
        StatusID=dblink, #db.TblStatuses
        PageHits='integer',
        DescriptionNoHtml='string',
    )

    alldefs["TblStatuses"] = dict(
        IIDD=dblink,
        Name='string',
    )

    alldefs["TblSuperAdmins"] = dict(
        IIDD=dblink,
        Name='string',
        Password='string',
    )

    #alldefs["TblSuperAdminsNickNames"] = dict(
        #IIDD='string',
        #NickName='string',
    #)

    alldefs["TblTerms"] = dict(
        IIDD=dblink,
        Name='string',
        TermTranslation='string',
        Background='string',
        InventedBy='string',
        InventedByMemberID=dblink, #db.TblMembers
        ObjectID=dblink, #db.TblObjects
        StatusID=dblink, #db.TblStatuses
        PageHits='integer',
        BackgroundNoHtml='string',
    )

    #alldefs["vw_displayableMembers"] = dict(
        #IIDD='string',
        #Name='string',
    #)

    #alldefs["vw_displayablePhotoIDs"] = dict(
        #PhotoID='string',
    #)

    #alldefs["vw_siteEventPhotosGroupedAndOrd"] = dict(
        #EventID='string',
        #FixedRandomValue='string',
    #)

    #alldefs["vw_siteEventPhotosHighestRanke1"] = dict(
        #EventID='string',
        #PhotoPath='string',
    #)

    #alldefs["vw_siteEventPhotosHighestRanked"] = dict(
        #EventID='string',
        #PhotoID='string',
    #)

    #alldefs["vw_siteEventPhotosOrderedByRan1"] = dict(
        #EventID='string',
        #FixedRandomValue='string',
        #EventPhotoRank='string',
    #)

    #alldefs["vw_siteEventPhotosOrderedByRank"] = dict(
        #EventID='string',
        #PhotoID='string',
        #EventPhotoRank='string',
        #RandomValue='string',
    #)

    #alldefs["vw_siteMemberPhotosGroupedAndOr"] = dict(
        #MemberID='string',
        #FixedRandomValue='string',
    #)

    #alldefs["vw_siteMemberPhotosHighestRank1"] = dict(
        #MemberID='string',
        #PhotoPath='string',
    #)

    #alldefs["vw_siteMemberPhotosHighestRanke"] = dict(
        #MemberID='string',
        #PhotoID='string',
    #)

    #alldefs["vw_siteMemberPhotosOrderedByRa1"] = dict(
        #MemberID='string',
        #FixedRandomValue='string',
        #MemberPhotoRank='string',
    #)

    #alldefs["vw_siteMemberPhotosOrderedByRan"] = dict(
        #MemberID='string',
        #PhotoID='string',
        #MemberPhotoRank='string',
        #RandomValue='string',
    #)

    return alldefs

def create_db_defs():
    out_name = '/home/haim/fossil_projects/gbs/private/db_defs.py'
    alldefs = fields_template()
    with open(out_name, 'w') as out:
        for tbl in sorted(alldefs):
            out.write("db.define_table('{}',\n".format(tbl))
            fields = alldefs[tbl]
            for field in sorted(fields):
                out.write("                Field('{}', type='{}'),\n".format(field, fields[field]))
            out.write(')\n\n')
        
if __name__ == '__main__':
    create_db_defs()       
