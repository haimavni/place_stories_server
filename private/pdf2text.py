from PyPDF2.pdf import PdfFileReader
import StringIO
import time

def pdf_to_text(filename):
    pdf = PdfFileReader(open(filename, "rb"))
    content = ""

    for i in range(0, pdf.getNumPages()):
        print str(i)
        extractedText = pdf.getPage(i).extractText()

        content +=  extractedText + "\n"

    content = " ".join(content.strip().split())
    #content = " ".join(content.replace("\xa0", " ").strip().split())
    return content.encode("utf-8", "ignore")


if __name__ == '__main__':

    path = '/home/haim/yoman.pdf'
    text = pdf_to_text(path)

    print text


