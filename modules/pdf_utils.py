# coding: utf-8

"""
pdf utils:
    convert pdf to html
    highlight words in pdf
"""
import re
# use poppler utils instead of the 2 below
## import fitz causes problems
import time
from gluon.storage import Storage

from pdf2image import convert_from_path
import pdfplumber
from .injections import inject
import psutil
import fitz

PAT = '[א-תךםןףץ]'
PAT_HEB = PAT.replace(']', ']{2,100}')
HEB_REGEX = re.compile(PAT_HEB, flags=re.U)
PAT_LAAZ = PAT.replace('[', '[^ ').replace(']', ']{2,100}')
LAAZ_REGEX = re.compile(PAT_LAAZ, flags=re.U)

def detect_rtl(doc):
    """
    some docs have their whole lines reversed and some have their words reversed.
    use position of commas to decide. ugly...
    """
    pat1 = PAT_HEB + ','
    pat2 = ',' + PAT_HEB
    regex1 = re.compile(pat1, flags=re.U)
    regex2 = re.compile(pat2, flags=re.U)
    n1 = 0
    n2 = 0
    for page in doc:
        text = page.getText()
        lst = text.split('\n')
        #make sure we are not biased by missing space between comma and the following word
        for tmp_s in lst:
            if regex1.search(tmp_s): 
                n1 += 1
            if regex2.search(tmp_s):
                n2 += 1
            if n1 - n2 > 10:
                return False
            elif n2 - n1 > 10:
                return True
    return n2 > n1

def pdf_to_text(pdfname, num_pages_extracted):
    comment, log_exception = inject('comment', 'log_exception')
    comment(f"about to open {pdfname}")
    num_pages_extracted = num_pages_extracted or 0
    result = ""
    num_pages = None
    n = 0
    m = 0
    try:
        pdf = pdfplumber.open(pdfname)
        comment("pdf was opened")
        num_pages = len(pdf.pages)
        for page in pdf.pages:
            if n < num_pages_extracted:
                n += 1
                continue
            text = ""
            mem = psutil.virtual_memory();
            comment(f"about to handle page {n}. memory percent: {mem.percent}")
            if mem.percent > 95:
                break;
            try:
                text = page.extract_text() or ''
                n += 1
                m += 1
                comment("page text was extracted")
            except Exception as e:
                comment(f"Exception! {e}")
                log_exception("error pdf to text")
                text = 'Page text could not be exctracted'
            ##comment(f"text extracted: {text}")
            result += text + '\n'
        comment(f"done with {pdfname}")
    except Exception as e:
        log_exception(f"error in pdf to text {result}")
    return Storage(text=result, num_pages_extracted=n, num_pages=num_pages)

def pdf_to_text(pdfname, num_pagesst_extracted):   
    doc = fitz.open(pdfname)  # open document
    result = ''
    num_pages_extracted = 0
    with open('/apps_data/gbs/logs/pdf-text.txt', 'w', encoding="utf-8") as f:
        for page in doc:  # iterate the document pages
            text = page.get_text() ##.encode("utf8")  # get plain text (is in UTF-8)
            f.write(text)
            lines = text.split('\n')
            text = ''
            for s in lines:
                s = s[::-1]
                text += s + ' '
            result += text
            result += chr(12)
            num_pages_extracted += 1
    return Storage(text=result, num_pages_extracted=num_pages_extracted, num_pages=num_pages_extracted)

def highlight_pdf(fname, outfname, keywords):
    """
    highlight keywords in pdf files
    """
    #currently does not work
    return
    # doc = fitz.open(fname)
    # if not isinstance(keywords, list):
    #     keywords = [keywords]
    # keywords = [w if isinstance(w, str) else w for w in keywords]
    # for kwd in keywords:
    #     if HEB_REGEX.match(kwd):
    #         kwd = reverse(kwd)
    #     for page in doc:
    #         text_instances = page.searchFor(kwd)
    #         for inst in text_instances:
    #             page.addHighlightAnnot(inst)
    # doc.save(outfname, garbage=4, deflate=True, clean=True)

def test_highlight():
    """
    test
    """
    fname = "/home/haim/pdf_tests/yoman.pdf"
    outfname = "/home/haim/yoman_highlighted.pdf"
    kw1 = "המונדיאל"
    kw2 = "המוסיקה"
    kw3 = "הנסיעה"
    kw4 = "המשפחות"
    highlight_pdf(fname, outfname, [kw1, kw2, kw3, kw4])

def test_pdf2text():
    import sys
    fname = sys.argv[1] if len(sys.argv) > 1 else 'yoman'
    '''test pdf to text'''
    pdfname = '/home/haim/pdf_tests/{}.pdf'.format(fname)
    html = pdf_to_text(pdfname)
    htmlname = pdfname.replace('.pdf', '.html')
    with open(htmlname, 'w') as tmp_f:
        tmp_f.write(html)
        
def save_pdf_jpg(pdf_path, jpg_path)        :
    pages = convert_from_path(pdf_path, dpi=20, last_page=1)
    pages[0].save(jpg_path, 'JPEG')
    
def test_pdf_jpg():
    import sys
    fname = sys.argv[1] if len(sys.argv) > 1 else 'yoman'
    '''test pdf to jpg'''
    pdf_name = '/home/haim/pdf_tests/{}.pdf'.format(fname)
    jpg_name = '/home/haim/pdf_tests/{}.jpg'.format(fname)
    save_pdf_jpg(pdf_name, jpg_name)

def reverse(tmp_s):
    """reverse string"""
    result = ''
    for tmp_c in tmp_s:
        result = tmp_c + result
    return result

def invert(match):
    """callback"""
    tmp_s = match.group(0)
    return reverse(tmp_s)

if __name__ == '__main__':
    test_pdf_jpg()
    test_pdf2text()
    test_highlight()
    print('done')


def fix_rtl(s):
    def rep(m):
        s = m.group(0)
        return s[::-1]

    rtl_chars = "[א-תךםןףץ]"
    ltr_chars = "[a-zA-z0-9](\s|[a-zA-z0-9])*[a-zA-z0-9]"
    m = re.search(rtl_chars, s)
    if m:
        s1 = s[::-1]
        s2 = re.sub(ltr_chars, rep, s1)
    else:
        s2 = s
    return s2

def experiments():
    s = 'ישראל נוסדה ב-8491. הפלישה החלה מיד.'
    s = s[::-1]
    s2 = fix_rtl(s)
    return dict(s=s, s2=s2)
