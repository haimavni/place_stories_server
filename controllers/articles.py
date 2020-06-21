@serve_json
def article_list():
    q = (db.TblObjects.deleted != True)
    lst = db(q).select()
    arr = [Storage(id=rec.id,
                   name=rec.name,
                   birth_date=rec.date_of_birth,
                   visibility=rec.visibility,
                   has_profile_photo=bool(rec.facePhotoURL), #used in client!
                   rnd=random.randint(0, 1000000),
                   facePhotoURL=photos_folder('profile_photos') + (rec.facePhotoURL or "dummy_face.png")) for rec in lst]
    arr.sort(key=lambda item: item.rnd)
    return arr

@serve_json
def remove_article(vars):
    article_id = int(vars.article_id)
    deleted = db(db.TblObjects.id == article_id).update(deleted=True) == 1
    if deleted:
        ws_messaging.send_message(key='ARTICLE_DELETED', group='ALL', article_id=article_id)
    return dict(deleted=deleted)

