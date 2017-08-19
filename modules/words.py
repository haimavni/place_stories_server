# coding: utf8

import re
from bs4 import BeautifulSoup
from guess_language import guessLanguage as guess
from langs import extract_words, language_name
from my_cache import Cache
from injections import inject
#from base64 import b64decode, b64encode
from math import log


alef = "א"
tav = "ת"

word_pat = r'([{alef}-{tav}]+|[0-9./]+|[a-zA-Z]+)'.format(alef=alef, tav=tav)
word_regex = re.compile(word_pat, re.UNICODE | re.MULTILINE)

def remove_all_tags(html):
    html = html.replace('>', '> ')  #to prevent words that are separated by tags only to stick together
    html = re.sub(r'&.{1,7};', ' ', html)
    soup = BeautifulSoup(html)
    text = soup.get_text()
    return text

def extract_tokens(s):
    s = remove_all_tags(s)
    ###lst = word_regex.findall(s, re.UNICODE | re.MULTILINE)
    return re.split(r'\s+', s)

def get_reisha(html, size=100):
    punctuation_marks = ',.;?!'
    lst = extract_tokens(html)
    result = ''
    for t in lst:
        if t not in punctuation_marks:
            result += ' '
        result += t
    return result

def guess_language(html):
    s = remove_all_tags(html)
    lang = guess(s)
    pattern = r'[א-ת]+'
    if lang != 'he' and lang != 'en':
        if isinstance(s, unicode):
            s = s.encode('utf8')
        m = re.search(pattern, s)
        if m:
            lang = 'he'
    if language_name(lang).endswith('?'):
        lang = 'UNKNOWN'
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
        SELECT TblWords.word, array_agg(TblWordStories.story_id), sum(TblWordStories.word_count)
        FROM TblWords, TblWordStories
        WHERE (TblWords.id = TblWordStories.word_id)
        GROUP BY TblWords.word;
    """

    lst = db.executesql(cmd)
    lst = sorted(lst, key=lambda item: abs(item[2] - 300), reverse=False)
    ##lst = sorted(lst, key=lambda item: item[2], reverse=True)
    ##lst = sorted(lst)  #todo: collect number of clicks and sort first by num of clicks then alfabetically

    result = [dict(name=item[0], story_ids=item[1], word_count=item[2]) for item in lst]
    return result

def update_words_index(story_id, dic, html=None):
    if not html:
        rec = db(db.TblStories.id==story_id).select().first()
        html = rec.story
    s = remove_all_tags(html)
    dic = dict()
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

    rec = db(db.TblWordStories.story_id==story_id).select().first()
    if rec:
        q = (db.TblWordStories.story_id==story_id) & (db.TblWords.id==db.TblWordStories.word_id)
        arr = db(q).select()
        #remove deleted links, add new ones, update existing ones
    else:
        for wrd in dic1:
            if wrd not in dic:
                word_id = db.TblWords.insert(word=wrd)
                db.TblWordStories.insert(story_id=story_id, word_id=word_id, word_count=dic1[w])
            else:
                word_id = db(db.TblWords.word==wrd).select().first().id
                rec = db((db.TblWordStories.story_id==story_id) & (db.TblWordStories.word_id==word_id)).select().first()
                if rec:
                    if rec.word_count != dic1[wrd]:
                        rec.update_record(word_count=dic1[wrd])
                else:
                    db.TblWordStories.insert(story_id=story_id, word_id=word_id, word_count=dic1[wrd])


def save_words_index(words_index, story_id, from_scratch=False):
    if from_scratch:
        db.TblWords.truncate('RESTART IDENTITY CASCADE')
    for wrd in words_index:
        rec = db(db.TblWords.word==wrd).select().first()
        if rec:
            word_id = rec.id
            stories = []
        else:
            word_id = db.TblWords.insert(word=wrd)
            stories = db(db.TblWordStories.word_id==word_id).select()
            stories = [rec.story_id for rec in stories]

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
