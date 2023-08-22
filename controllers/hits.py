import datetime


@serve_json
def count_hit(vars):
    what = vars.what.upper()
    date = datetime.datetime.today()
    item_id = int(vars.item_id)
    rec = db(
        (db.TblPageHits.what == what) &
        (db.TblPageHits.date == date) &
        (db.TblPageHits.item_id == item_id)).select().first()
    if rec:
        rec.update_record(count=rec.count + 1,
                          new_count=(rec.new_count or 0) + 1)
    else:
        db.TblPageHits.insert(what=what, item_id=item_id,
                              date=date, count=1, new_count=1)
    return dict()


@serve_json
def get_hit_statistics(vars):
    end_date = vars.end_date if vars.end_date else datetime.datetime.today()
    periods = [1, 7, 30, 0]
    end_date = end_date - datetime.timedelta(days=1)
    result = dict()
    # whats = db(db.TblPageHits).select(db.TblPageHits.what, groupby=db.TblPageHits.what)
    # whats = [w.what for w in whats]
    tables = dict(
        APP=None,
        MEMBER=db.TblMembers,
        EVENT=db.TblEvents,
        PHOTO=db.TblPhotos,
        TERM=db.TblTerms,
        DOC=db.TblDocs,
        DOCSEG=db.TblDocSegments,
        VIDEO=db.TblVideos
    )
    for what in tables:
        totals = dict()
        detailed = dict()
        tbl = tables[what]
        for period in periods:
            start_date = end_date - datetime.timedelta(days=period)
            if period == 1:
                q = db.TblPageHits.date == end_date
            elif period:
                q = (db.TblPageHits.date >= start_date) & (
                    db.TblPageHits.date <= end_date)
            else:
                q = db.TblPageHits.id > 0
            q &= (db.TblPageHits.count != None)
            q &= (db.TblPageHits.what == what)
            prec = db(q).select(db.TblPageHits.count.sum()).first()
            totals[period] = prec._extra['SUM("TblPageHits"."count")']
            if not tbl:
                continue
            if tbl:
                q &= (tbl.story_id==db.TblStories.id)
            q &= (db.TblPageHits.item_id == tbl.id)
            q &= (db.TblStories.deleted != True)
            precs = db(q).select(db.TblPageHits.item_id, tbl.name, db.TblPageHits.count.sum(),
                                 groupby=[db.TblPageHits.item_id, db.TblStories.name],
                                 orderby=~db.TblPageHits.count.sum())
            detailed[period] = [parse(prec, tbl) for prec in precs]
        result[what] = dict(totals=totals, detailed=detailed)
    return result


def parse(prec, tbl_name):
    return dict(count=prec._extra['SUM("TblPageHits"."count")'],
                name=prec[tbl_name].name,
                item_id=prec.TblPageHits.item_id
                )
