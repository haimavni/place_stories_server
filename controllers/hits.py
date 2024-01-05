import datetime


@serve_json
def count_hit(vars):
    what = vars.what.upper()
    date = datetime.datetime.today()
    id = int(vars.item_id)
    item_id, story_id = item_and_story_ids(what, id)
    if not (item_id and story_id):
        comment(f"!!!!!!!!!!!! missing item_id or story_id: {item_id} / {story_id}!!!!!!")
        return dict()
    rec = db(
        (db.TblPageHits.what == what) &
        (db.TblPageHits.date == date) &
        (db.TblPageHits.item_id == item_id)).select().first()
    if rec:
        rec.update_record(count=rec.count + 1,
                          new_count=(rec.new_count or 0) + 1)
    else:
        db.TblPageHits.insert(what=what, item_id=item_id, story_id=story_id,
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
    tables = get_tables_dic()
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
            q &= (db.TblPageHits.item_id == tbl.id) #todo: use story_id?
            q &= (db.TblStories.deleted != True)
            precs = db(q).select(db.TblPageHits.item_id, db.TblPageHits.story_id, db.TblStories.name, db.TblPageHits.count.sum(),
                                 groupby=[db.TblPageHits.item_id, db.TblPageHits.story_id, db.TblStories.name],
                                 orderby=~db.TblPageHits.count.sum())
            detailed[period] = [parse(prec, what) for prec in precs]
        result[what] = dict(totals=totals, detailed=detailed)
    return result


def parse(prec, what):
    return dict(count=prec._extra['SUM("TblPageHits"."count")'],
                name=prec.TblStories.name,
                item_id=prec.TblPageHits.item_id,
                story_id=prec.TblPageHits.story_id,
                url=calc_item_url(what, prec.TblPageHits)
                )
    
def calc_item_url(what, rec):
    host, app = calc_host_and_app()
    if what == "MEMBER":
        return f"https://{host}/{app}/aurelia#/member-details/{rec.item_id}/*"
    if what == "EVENT":
        return f"https://{host}/{app}/aurelia#/story-detail/{rec.story_id}/*"
    if what == "PHOTO":
        return f"https://{host}/{app}/aurelia#/photos/{rec.item_id}/*"
    if what == "TERM":
        return f"https://{host}/{app}/aurelia#/term-detail/{rec.story_id}/*"
    if what == "DOC":
         return f"https://{host}/{app}/aurelia#/doc-detail/{rec.item_id}/*"
    if what == "DOCSEG":
         return f"https://{host}/{app}/aurelia#/doc-detail/1/*?caller=docs&segment_id={rec.item_id}"
    if what == "VIDEO":
        return f"https://{host}/{app}/aurelia#/annotate-video/{rec.item_id}/*"
    
def calc_host_and_app():
    host = request.env.HTTP_HOST
    app = request.application
    return host, app

def get_tables_dic():
    return dict(
        APP=None,
        MEMBER=db.TblMembers,
        EVENT=db.TblEvents,
        PHOTO=db.TblPhotos,
        TERM=db.TblTerms,
        DOC=db.TblDocs,
        DOCSEG=db.TblDocSegments,
        VIDEO=db.TblVideos
    )
    
def item_and_story_ids(what, id):
    tbls = get_tables_dic()
    tbl = tbls[what]
    if not tbl:
        return None, None
    if what == "EVENT" or what == "TERM":
        story_id = id
        rec = db(tbl.story_id==story_id).select().first()
        if rec:
            item_id = rec.id
        else:
            item_id = None
    else:
        item_id = id
        rec = db(tbl.id==id).select().first()
        if rec:
            story_id = rec.story_id
        else:
            story_id = None
    return item_id, story_id