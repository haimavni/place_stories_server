# coding: utf8

import re
from bs4 import BeautifulSoup
from langs import extract_words, language_name
from langdetect import detect, detect_langs
from my_cache import Cache
from injections import inject
#from base64 import b64decode, b64encode
from math import log
import datetime
import ws_messaging

alef = "א"
tav = "ת"

word_pat = r'([{alef}-{tav}]+|[0-9./]+|[a-zA-Z]+)'.format(alef=alef, tav=tav)
word_regex = re.compile(word_pat, re.UNICODE | re.MULTILINE)

def remove_all_tags(html):
    html = html.replace('>', '> ')  #to prevent words that are separated by tags only to stick together
    ##html = re.sub(r'&quot;', '"', html)
    ##html = re.sub(r'&#39;', "'", html)
    ##html = re.sub(r'&.{1,7};', ' ', html)
    html = re.sub(r'&#?[a-z0-9]+;([a-z]+;)*', ' ', html)
    soup = BeautifulSoup(html)
    text = soup.get_text()
    return text

def extract_tokens(s):
    s = remove_all_tags(s)
    ###lst = word_regex.findall(s, re.UNICODE | re.MULTILINE)
    lst = re.split(r'\s+', s)
    #remove quotes unless they are apostrophes
    for qu in ['"', "'"]:
        q0 = -1
        for i, w in enumerate(lst):
            if w.startswith(qu):
                q0 = i
            if w.endswith(qu):
                if q0 > 0:
                    lst[q0] = lst[q0][1:]
                    lst[i] = w[:-1]
            q0 = -1;
            
    return lst

def get_reisha(html, size=60):
    punctuation_marks = ',.;?!'
    lst = extract_tokens(html)
    result = ''
    for i, t in enumerate(lst):
        if i > size:
            break
        if t not in punctuation_marks:
            result += ' '
        result += t
    result += '...'
    return result

def guess_language(html):
    s = remove_all_tags(html)
    try:
        lang = detect(s)
    except:
        return 'UNKNOWN'
    return lang

def tally_words(html, dic, story_id, story_name):
    s = story_name.decode('utf8') + ' ' + remove_all_tags(html)
    lst = extract_words(s)
    if not lst:
        return False
    dic1 = dict()
    for w in lst:
        if w not in dic:
            dic[w] = {}
        if story_id not in dic[w]:
            dic[w][story_id] = 0
        dic[w][story_id] += 1
        if w not in dic1:
            dic1[w] = 0
        dic1[w] += 1
    return True

def extract_story_words(story_id):
    from injections import inject
    db = inject('db')
    rec = db(db.TblStories.id==story_id).select().first()
    if not rec:
        return None
    story_name = rec.name
    html = rec.story
    s = story_name.decode('utf8') + ' ' + remove_all_tags(html)
    lst = extract_words(s)
    if not lst:
        return None
    dic = dict()
    for w in lst:
        if w not in dic:
            dic[w] = 0
        dic[w] += 1
    return dic

def retrieve_story_words(story_id):
    from injections import inject
    db = inject('db')
    q = (db.TblWordStories.story_id==story_id) & (db.TblWords.id==db.TblWordStories.word_id)
    lst = db(q).select()
    dic = dict()
    for rec in lst:
        w = rec.TblWords.word
        dic[w] = rec.TblWordStories.word_count
    return dic

def update_story_words_index(story_id):
    from injections import inject
    now = datetime.datetime.now()
    added_words = []
    deleted_words = []
    db = inject('db')
    old_dic = retrieve_story_words(story_id)
    new_dic = extract_story_words(story_id) or {}
    new_words = {}
    for w in new_dic:
        word_id, new = find_or_insert_word(w)
        if new:
            new_words[word_id] = w
        if w not in old_dic:
            db.TblWordStories.insert(story_id=story_id, word_id=word_id, word_count=new_dic[w])
            added_words.append(word_id)
        elif new_dic[w] != old_dic[w]:
            db((db.TblWordStories.word_id==word_id) & (db.TblWordStories.story_id==story_id)).update(word_count=new_dic[w])
            #for now we do not broadcast modified word count
    for w in old_dic:
        if w not in new_dic:
            word_id, new = find_or_insert_word(w) #it will not be inserted...
            deleted_words.append(word_id)
            db((db.TblWordStories.word_id==word_id) & (db.TblWordStories.story_id==story_id)).delete()
    ws_messaging.send_message('WORD_INDEX_CHANGED', group='ALL', 
                              story_id=story_id, added_words=added_words, deleted_words=deleted_words, new_words=new_words)
    db(db.TblStories.id==story_id).update(indexing_date=now)
            
def find_or_insert_word(wrd):            
    from injections import inject
    db = inject('db')
    rec = db(db.TblWords.word==wrd).select().first()
    if rec:
        return rec.id, False
    else:
        return db.TblWords.insert(word=wrd), True

def tally_all_stories():   
    from injections import inject
    db = inject('db')
    dic = dict()
    N = 0
    for rec in db(db.TblStories).select():
        html = rec.story
        if tally_words(html, dic, rec.id, rec.name):
            N += 1
    return dic

def create_word_index():
    import datetime
    t0 = datetime.datetime.now()
    db = inject('db')
    db.TblWords.truncate('RESTART IDENTITY CASCADE')
    dic = tally_all_stories()
    for wrd in dic:
        word_id = db.TblWords.insert(word=wrd)
        for story_id in dic[wrd]:
            db.TblWordStories.insert(word_id=word_id, story_id=story_id, word_count=dic[wrd][story_id])
    elapsed = datetime.datetime.now() - t0
    db.commit()
    print elapsed

def read_words_index():
    db = inject('db')

    cmd = """
        SELECT TblWords.id, TblWords.word, array_agg(TblWordStories.story_id), sum(TblWordStories.word_count)
        FROM TblWords, TblWordStories
        WHERE (TblWords.id = TblWordStories.word_id)
        GROUP BY TblWords.word, TblWords.id;
    """

    lst = db.executesql(cmd)
    lst = sorted(lst, key=lambda item: item[1], reverse=False)
    ##lst = sorted(lst, key=lambda item: item[2], reverse=True)
    ##lst = sorted(lst)  #todo: collect number of clicks and sort first by num of clicks then alfabetically

    result = [dict(word_id=item[0], name=item[1], story_ids=item[2], word_count=item[3]) for item in lst]
    return result

def _calc_used_languages(used_for):
    db = inject('db')
    dic = {}
    q = (db.TblStories.id > 0)
    if used_for:
        q &= (db.TblStories.used_for==used_for)
    for rec in db(q).select():
        lang = rec.language
        if lang not in dic:
            dic[lang] = 0
        dic[lang] += 1
    lst = []
    for lang in sorted(dic):
        item = dict(id=lang, name='stories.' + language_name(lang), count=dic[lang])
        lst.append(item)
    return dict(used_languages=lst)

def calc_used_languages(vars, refresh=False):
    used_for = int(vars.used_for) if vars.used_for else 2 #STORY4EVENT
    c = Cache('used_languages' + str(used_for))
    return c(lambda: _calc_used_languages(used_for), refresh)

def _get_all_story_previews():
    db = inject('db')
    result = []
    for rec in db(db.TblStories).select(orderby=~db.TblStories.story_len):
        html = rec.story
        preview = get_reisha(html, 30)
        result.append(dict(name=rec.name, id=rec.id, prview=preview))
    return result

def get_all_story_previews(refresh=False):
    c = Cache('get_all_story_previews')
    return c(_get_all_story_previews, refresh)

def test():
    html = 'חיים אבני כותב תוכנית מחשב computer program'
    tally_words

if __name__ == '__main__'    :
    test()
