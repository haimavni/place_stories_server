# coding: utf-8

"""
pdf utils:
    convert pdf to html
    highlight words in pdf
"""
import re
# use poppler utils instead of the 2 below
## import fitz causes problems
from pdf2image import convert_from_path
import pdfplumber
from .injections import inject

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

def pdf_to_text(pdfname):
    comment, log_exception = inject('comment', 'log_exception')
    comment(f"about to open {pdfname}")
    result = ""
    try:
        pdf = pdfplumber.open(pdfname)
        comment("pdf was opened")
        for page in pdf.pages:
            text = ""
            comment("about to handle page")
            text = page.extract_text() or ''
            comment(f"text extracted: {text}")
            result += text + '\n'
        comment(f"done with {pdfname}")
    except Exception as e:
        log_exception(f"error pdf to text {result}")
    return result

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
