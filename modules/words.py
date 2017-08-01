# coding: utf8

import re
from bs4 import BeautifulSoup
from guess_language import guessLanguage as guess
from langs import extract_words, language_name
from my_cache import Cache
from injections import inject

alef = "א"
tav = "ת"

word_pat = r'([{alef}-{tav}]+|[0-9./]+|[a-zA-Z]+)'.format(alef=alef, tav=tav)
word_regex = re.compile(word_pat, re.UNICODE | re.MULTILINE)

def remove_all_tags(html):
    html = html.replace('>', '> ')  #to prevent words that are separated by tags only to stick together
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

def tally_words(html, dic, story_id):
    s = remove_all_tags(html)
    lst = extract_words(s)
    for w in lst:
        if w not in dic:
            dic[w] = {}
        if story_id not in dic[w]:
            dic[w][story_id] = 0
        dic[w][story_id] += 1

def _tally_all_stories():   
    from injections import inject
    db = inject('db')
    dic = {}
    for rec in db(db.TblStories).select():
        html = rec.story
        tally_words(html, dic, rec.id)
    #todo: use tfidf to rank words?
    return dic

def tally_all_stories(refresh=False):
    c = Cache('tally_all_stories')
    return c(_tally_all_stories, refresh)
    
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
    



