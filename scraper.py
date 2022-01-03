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
import os
import yaml


with open("config.yaml", 'r') as stream:
    data_loaded = yaml.safe_load(stream)
    print(data_loaded)

fileName = data_loaded['filePath']
firstPageToLoad = 2
isMarkscheme = True if fileName[len(
    fileName) - 14: len(fileName)] == 'markscheme.pdf' else False
if (isMarkscheme):
    print("Is MS")
startPageNum = 2

listOfData = []


# Get image dimensions and scale max x, y accordingly
doc = fitz.open(fileName)
page = doc.load_page(2)
ir = fitz.IRect(0, 0, 9999, 9999)
pix = page.get_pixmap(dpi=300, clip=ir)
output = "sample" + ".png"
pix.save(output)
image = Image.open('sample.png')
width, height = image.size
maxWidthUnits = (width/2677)*643
maxHeightUnits = (height/3704)*890
os.remove('sample.png')


def get_text_coordinates(o: Any, depth=0) -> list:
    global listOfData

    v = get_optional_text(o)
    if (len(v) > 1):
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


file = open(fileName, 'rb')
parser = PDFParser(file)
document = PDFDocument(parser)
pdfLen = resolve1(document.catalog['Pages'])['Count']

pagesData = {}


def generate_data():
    for i in range(firstPageToLoad, pdfLen + 1):
        global listOfData
        listOfData = []
        page = extract_pages(fileName, page_numbers=[i])
        pageData = get_text_coordinates(page)
        pagesData[i] = pageData


generate_data()

questionDataBank = {
    # question number: question number, coordinates, page number
}


maxQuestionNum = 0


def find_start() -> bool:
    global startPageNum
    for i in range(firstPageToLoad, pdfLen + 1):
        for d in pagesData[i]:
            if ((d[0].strip()).upper() == 'SECTION A'):
                startPageNum = i
                print("Start page = " + str(i))
                return True
    print("Error: Could not find start")
    return False


find_start()


def get_first_word(str: str) -> str:
    firstCharPos = 0
    for i in range(0, len(str)):
        if (str[i] != ' '):
            firstCharPos = i
            break

    lastCharPos = None
    for i in range(firstCharPos, len(str)):
        if (str[i] == ' '):
            lastCharPos = i
            break

    return str[firstCharPos: lastCharPos]


def find_questions():
    global maxQuestionNum
    questionNumCount = 1
    for i in range(startPageNum, pdfLen + 1):
        for d in pagesData[i]:
            questionStr = str(questionNumCount) + "."
            if (d[0] == questionStr or get_first_word(d[0]) == questionStr):
                questionDataBank[questionNumCount] = [
                    questionNumCount, d[1], i]
                if (questionNumCount > maxQuestionNum):
                    maxQuestionNum = questionNumCount
                questionNumCount += 1


find_questions()
# print(questionDataBank)


def pos_to_IRect(posarr) -> IRect:
    global maxHeightUnits
    newx1 = posarr[0]
    newy1 = maxHeightUnits - posarr[1]
    newx2 = posarr[2]
    newy2 = maxHeightUnits - posarr[3]
    if (newx1 > newx2):
        temp = newx2
        newx2 = newx1
        newx1 = temp
    if (newy1 > newy2):
        temp = newy2
        newy2 = newy1
        newy1 = temp
    #print(newx1, newy1, newx2, newy2)
    return fitz.IRect(newx1, newy1, newx2, newy2)


doc = fitz.open(fileName)


def generate_images():
    global doc, questionDataBank, maxQuestionNum
    for i in range(1, maxQuestionNum+1):
        if (i in questionDataBank):
            q = questionDataBank[i]

            if (i+1 <= maxQuestionNum and i+1 in questionDataBank):
                nextq = None
                nextq = questionDataBank[i+1]
                for i in range(q[2], nextq[2] + 1):
                    if (nextq[2] == i and i != q[2]):
                        break
                    if (nextq[2] == i):
                        y1 = nextq[1][3] + 10
                    else:
                        y1 = 20
                    page = doc.load_page(i)
                    coordinates = q[1]
                    if (i == q[2]):
                        y2 = coordinates[3]
                    else:
                        y2 = maxHeightUnits
                    ir = pos_to_IRect([0, y1, 9999, y2+20])
                    pix = page.get_pixmap(dpi=300, clip=ir)
                    output = "question"+str(q[0]) + "_p" + str(i + 1) + ".png"
                    pix.save(output)

            else:
                # TODO, add support for multi-page questions for last question
                page = doc.load_page(q[2])
                # Width of page = 643, height of page = 890 units
                c = q[1]
                y1 = 100

                y2 = c[3]

                ir = pos_to_IRect([0, y1, 590, y2+20])

                pix = page.get_pixmap(dpi=300, clip=ir)
                output = "question"+str(q[0]) + ".png"
                pix.save(output)


generate_images()
