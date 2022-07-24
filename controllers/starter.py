from gluon.utils import web2py_uuid

@serve_json
def get_constants(vars):
    return dict(
        story_type=dict(
            STORY4MEMBER=STORY4MEMBER,
            STORY4EVENT=STORY4EVENT,
            STORY4PHOTO=STORY4PHOTO,
            STORY4TERM=STORY4TERM,
            STORY4MESSAGE=STORY4MESSAGE,
            STORY4HELP=STORY4HELP,
            STORY4FEEDBACK=STORY4FEEDBACK,
            STORY4DOC=STORY4DOC,
            STORY4VIDEO=STORY4VIDEO,
            STORY4AUDIO=STORY4AUDIO,
            STORY4ARTICLE=STORY4ARTICLE
        ),
        visibility=dict(
            VIS_NEVER=VIS_NEVER,
            # for non existing members such as the child of a childless couple (it just connects the)
            VIS_NOT_READY=VIS_NOT_READY,
            VIS_VISIBLE=VIS_VISIBLE,
            VIS_HIGH=VIS_HIGH
        ),
        cause_of_death=dict(
            DC_DIED=0,
            DC_FELL=1,
            DC_KILLED=2,
            DC_MURDERED=3
        ),
        story_visibility=dict(
            SV_NO_CHANGE=SV_NO_CHANGE,
            SV_PUBLIC=SV_PUBLIC,
            SV_ADMIN=SV_ADMIN_ONLY,
            SV_ARCHIVER=SV_ARCHIVER_ONLY,
            SV_LOGGEDIN=SV_LOGGEDIN_ONLY
        ),
        ptp_key=web2py_uuid()
    )
