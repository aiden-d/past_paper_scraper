import fitz
from PIL import Image
from fitz.fitz import IRect

doc = fitz.open('sample_cs.pdf')
page = doc.load_page(2)
ir = fitz.IRect(0, 0, 800, 1500)
# TODO problem is that the different papers have different max coordinates, so we need to scale the max coordinates based on a max picture dimensions.
pix = page.get_pixmap(dpi=300, clip=ir)
output = "deez1" + ".png"
pix.save(output)
