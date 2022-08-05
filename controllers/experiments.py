import ws_messaging
def test1():
    lst = db(db.auth_user.id>0).select()
    cmd = db._lastsql
    cmd = """
         SELECT TblWords.id, TblWords.word, array_agg(TblWordStories.story_id), sum(TblWordStories.word_count)
         FROM TblWords, TblWordStories
         WHERE (TblWords.id = TblWordStories.word_id)
         GROUP BY TblWords.word, TblWords.id;
     """
    cmd = """
            SELECT "TblWords"."id", "TblWords"."word", array_agg("TblWordStories"."story_id"), sum("TblWordStories"."word_count")
            FROM "TblWords", "TblWordStories"
            WHERE ("TblWords"."id" = "TblWordStories"."word_id")
            GROUP BY "TblWords"."word", "TblWords"."id";
        """
    lst = db.executesql(cmd)
    lst = db(db.TblWords.id==db.TblWordStories.word_id).select(db.TblWords.id, db.TblWords.word,\
            groupby=[db.TblWords.word,db.TblWords.id])
    cmd = db._lastsql
    return cmd

def test_2():
    ws_messaging.send_message(key='TEST', group='ALL', user_id=2, data="one two three")

