import fitz
from PIL import Image
from fitz.fitz import IRect
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pathlib import Path
from typing import Iterable, Any
from pdfminer.high_level import extract_pages
from pdfminer.pdfinterp import resolve1
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage


listOfData = []


def get_text_coordinates(o: Any, depth=0) -> list:
    global listOfData

    v = get_optional_text(o)
    if (len(v) > 1 and len(v) < 20):
        listOfData.append([get_optional_text(o), get_optional_bbox(o)])

    if isinstance(o, Iterable):
        for i in o:
            w = get_text_coordinates(i, depth=depth + 1)
            # if (w != []):
            #    listOfData.append(w)
    return listOfData


def get_indented_name(o: Any, depth: int) -> str:
    # Indented name of LTItem
    return '  ' * depth + o.__class__.__name__

# TODO find a way to export these values as a 2D array


def get_optional_bbox(o: Any) -> str:
    # Coordinates of the text
    arr = []
    if hasattr(o, 'bbox'):
        for i in o.bbox:
            arr.append(int(i))
        return arr
    return ''


def get_optional_text(o: Any) -> str:
    # Text value
    if hasattr(o, 'get_text'):
        return o.get_text().strip()
    return ''


fileName = 'sample_math.pdf'
# pageNum = 4
# text = convert_pdf_to_txt(fileName, pageNum)
# print(text)
file = open(fileName, 'rb')
parser = PDFParser(file)
document = PDFDocument(parser)
pdfLen = resolve1(document.catalog['Pages'])['Count']

pagesData = {}


def generate_data():
    qNum = 0
    for i in range(2, pdfLen + 1):
        global listOfData
        listOfData = []
        page = extract_pages(fileName, page_numbers=[i])
        pageData = get_text_coordinates(page)
        pagesData[i] = pageData


        # for d in pageData:
        #     if d[0] == '1.':
        #         print(d)
generate_data()
# print(pagesData)

questionDataBank = {
    # question number: question number, coordinates, page number
}

# print(pagesData[4])

maxQuestionNum = 0


def find_questions():
    global maxQuestionNum
    questionNumCount = 1
    for i in range(2, pdfLen + 1):
        for d in pagesData[i]:
            questionStr = str(questionNumCount) + "."
            if (d[0] == questionStr):
                questionDataBank[questionNumCount] = [
                    questionNumCount, d[1], i]
                if (questionNumCount > maxQuestionNum):
                    maxQuestionNum = questionNumCount
                questionNumCount += 1


find_questions()
print(questionDataBank)


def pos_to_IRect(posarr) -> IRect:
    newx1 = posarr[0]
    newy1 = 890 - posarr[1]
    newx2 = posarr[2]
    newy2 = 890 - posarr[3]
    if (newx1 > newx2):
        temp = newx2
        newx2 = newx1
        newx1 = temp
    if (newy1 > newy2):
        temp = newy2
        newy2 = newy1
        newy1 = temp
    print(newx1, newy1, newx2, newy2)
    return fitz.IRect(newx1, newy1, newx2, newy2)


doc = fitz.open(fileName)


def generate_images():
    global doc, questionDataBank, maxQuestionNum
    for i in range(1, maxQuestionNum+1):
        q = questionDataBank[i]
        nextq = None
        if (i+1 <= maxQuestionNum):
            nextq = questionDataBank[i+1]

        page = doc.load_page(q[2])
        # Width of page = 643, height of page = 890 units
        c = q[1]
        y1 = 100
        if (nextq != None and q[2] == nextq[2]):
            y1 = nextq[1][3] + 10

        y2 = c[3]
        ir = pos_to_IRect([0, y1, 590, y2+20])

        pix = page.get_pixmap(dpi=300, clip=ir)
        output = "question"+str(q[0]) + ".png"
        pix.save(output)


generate_images()
