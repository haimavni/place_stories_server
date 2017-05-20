def fields_template():

    alldefs = dict()

    alldefs["vw_siteMemberPhotosHighestRank1"] = dict(
        MemberID='string',
        PhotoPath='string',
    )

    alldefs["vw_siteEventPhotosHighestRanked"] = dict(
        EventID='string',
        PhotoID='string',
    )

    alldefs["vw_siteMemberPhotosGroupedAndOr"] = dict(
        MemberID='string',
        FixedRandomValue='string',
    )

    alldefs["TblDefaults"] = dict(
        ID='string',
        AdminMaxResultsInPage='string',
        UserMaxResultsInPage='string',
        PhotosInMember='string',
        PhotosInEvent='string',
        NormalPhotoWidth='string',
        ThumbnailPhotoWidth='string',
        AdminThumbnailPhotoHeight='string',
        UserMaxRandomEventsInMainPage='string',
        PageHitsCountingStatus='string',
        CommentsEmailName='string',
        CommentsEmailAddress='string',
        IdentifyEmailName='string',
        IdentifyEmailAddress='string',
        MailHost='string',
        MailPort='string',
        MailFromAddress='string',
        MailFromName='string',
        UserMaxPhotosInUnidentifiedPage='string',
        AdminHrefInitialAddress='string',
    )

    alldefs["TblHrefTypes"] = dict(
        ID='string',
        Name='string',
    )

    alldefs["TblPhotos"] = dict(
        ID='string',
        ArchiveNum='string',
        PhotoDate='string',
        Name='string',
        Description='string',
        Photographer='string',
        KeyWords='string',
        LocationInDisk='string',
        PhotoRank='string',
        ObjectID='string',
        Recognized='string',
        StatusID='string',
        PageHits='string',
        DescriptionNoHtml='string',
    )

    alldefs["vw_siteMemberPhotosHighestRanke"] = dict(
        MemberID='string',
        PhotoID='string',
    )

    alldefs["TblHrefCategories"] = dict(
        ID='string',
        Name='string',
        CategoryRank='string',
    )

    alldefs["TblSuperAdmins"] = dict(
        ID='string',
        Name='string',
        Password='string',
    )

    alldefs["TblDocuments"] = dict(
        ID='string',
        ArchiveNum='string',
        DocumentDate='string',
        Description='string',
        LocationInDisk='string',
        StatusID='string',
    )

    alldefs["TblAdmins"] = dict(
        ID='string',
        Name='string',
        Password='string',
    )

    alldefs["TblFamilyConnectionTypes"] = dict(
        ID='string',
        Description='string',
    )

    alldefs["TblTerms"] = dict(
        ID='string',
        Name='string',
        TermTranslation='string',
        Background='string',
        InventedBy='string',
        InventedByMemberID='string',
        ObjectID='string',
        StatusID='string',
        PageHits='string',
        BackgroundNoHtml='string',
    )

    alldefs["vw_siteEventPhotosOrderedByRank"] = dict(
        EventID='string',
        PhotoID='string',
        EventPhotoRank='string',
        RandomValue='string',
    )

    alldefs["TblHrefCategoryCategories"] = dict(
        ChildCategoryID='string',
        ParentCategoryID='string',
        ChildHierarchyLevel='string',
    )

    alldefs["TblStatuses"] = dict(
        ID='string',
        Name='string',
    )

    alldefs["TblMemberPhotos"] = dict(
        MemberID='string',
        PhotoID='string',
        MemberPhotoRank='string',
    )

    alldefs["vw_siteEventPhotosOrderedByRan1"] = dict(
        EventID='string',
        FixedRandomValue='string',
        EventPhotoRank='string',
    )

    alldefs["vw_siteEventPhotosGroupedAndOrd"] = dict(
        EventID='string',
        FixedRandomValue='string',
    )

    alldefs["vw_siteEventPhotosHighestRanke1"] = dict(
        EventID='string',
        PhotoPath='string',
    )

    alldefs["TblEventMembers"] = dict(
        EventID='string',
        MemberID='string',
        EventMemberRank='string',
    )

    alldefs["TblEventTypes"] = dict(
        ID='string',
        Name='string',
        Description='string',
        ImageName='string',
    )

    alldefs["TblSuperAdminsNickNames"] = dict(
        ID='string',
        NickName='string',
    )

    alldefs["/home/haim/fossil_projects/gbs/private/old_db/eggs"] = dict(
        ID='string',
        ArchiveNum='string',
        PhotoDate='string',
        Name='string',
        Description='string',
        Photographer='string',
        KeyWords='string',
        LocationInDisk='string',
        PhotoRank='string',
        ObjectID='string',
        Recognized='string',
        StatusID='string',
        PageHits='string',
        DescriptionNoHtml='string',
    )

    alldefs["TblObjects"] = dict(
        ID='string',
        Description='string',
        Priority='string',
        HebrewDescription='string',
    )

    alldefs["vw_displayablePhotoIDs"] = dict(
        PhotoID='string',
    )

    alldefs["TblMemberDocuments"] = dict(
        MemberID='string',
        DocumentID='string',
        MemberDocumentRank='string',
    )

    alldefs["TblJokes"] = dict(
        ID='string',
        Description='string',
    )

    alldefs["TblHrefCategoryHrefs"] = dict(
        HrefID='string',
        CategoryID='string',
    )

    alldefs["TblHrefs"] = dict(
        ID='string',
        Name='string',
        Description='string',
        Href='string',
        HrefTypeID='string',
        HrefRank='string',
        DescriptionNoHtml='string',
    )

    alldefs["TblEvents"] = dict(
        ID='string',
        Name='string',
        Source='string',
        EventDate='string',
        Place='string',
        Description='string',
        KeyWords='string',
        EventRank='string',
        TypeID='string',
        ObjectID='string',
        StatusID='string',
        PageHits='string',
        DescriptionNoHtml='string',
    )

    alldefs["vw_displayableMembers"] = dict(
        ID='string',
        Name='string',
    )

    alldefs["TblMembers"] = dict(
        ID='string',
        Name='string',
        FormerName='string',
        DateOfBirth='string',
        PlaceOfBirth='string',
        DateOfAlia='string',
        DateOfMember='string',
        Education='string',
        Institute='string',
        Professions='string',
        LifeStory='string',
        KeyWords='string',
        ObjectID='string',
        NickName='string',
        StatusID='string',
        PageHits='string',
        LifeStoryNoHtml='string',
    )

    alldefs["TblEventDocuments"] = dict(
        EventID='string',
        DocumentID='string',
        EventDocumentRank='string',
    )

    alldefs["TblEventPhotos"] = dict(
        EventID='string',
        PhotoID='string',
        EventPhotoRank='string',
    )

    alldefs["vw_siteMemberPhotosOrderedByRa1"] = dict(
        MemberID='string',
        FixedRandomValue='string',
        MemberPhotoRank='string',
    )

    alldefs["vw_siteMemberPhotosOrderedByRan"] = dict(
        MemberID='string',
        PhotoID='string',
        MemberPhotoRank='string',
        RandomValue='string',
    )

    alldefs["TblMemberConnections"] = dict(
        ID='string',
        MemberID='string',
        ConnectToMemberID='string',
        ConnectionTypeID='string',
        Name='string',
        DateOfBirth='string',
        PlaceOfBirth='string',
        Professions='string',
    )

    return alldefs