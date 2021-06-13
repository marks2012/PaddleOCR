# -*- coding:UTF-8 -*-
# parse files, including ocr,
import requests
import fitz
from PIL import Image
from paddleocr import PaddleOCR

class pdf_parsor():
    def __init__(self, url):
        #self.file_id = file_id
        self.url = url
        self.path = './doc/pdf/temp/'

    def download_file(self):
        r = requests.get(self.url)
        file_type = self.url.split('.')[-1]
        file_name = self.url.split('/')[-1]
        with open(self.path + file_name, "wb") as code:
            code.write(r.content)
        return self.path + file_name

    def pdf_parse(self, path):
        doc = fitz.open(path)
        ocr_engine = PaddleOCR()
        for page in doc:
            print('Process page: %s'%page.number)
            for link in page.links():
                print('link: %s'%link)
            for annot in page.annots():
                print('annotations: %s'%annot)
            for field in page.widgets():
                print('field: %s'%field)
            pix = page.get_pixmap()
            pix.save(self.path + "page-%i.png" % page.number)
            ocr_text = ocr_engine.ocr(self.path + "page-%i.png" % page.number)

            text = page.get_text("text")
            print('text: %s'%text)

            paragraph = page.get_text("blocks")
            print('blocks:%s'%paragraph)

            words = page.get_text("words")
            print('words:%s' % words)

        return True
        

class word_parsor():
    def __init__(self):
        return True

class excel_parsor():
    def __init__(self):
        return True

class text_parsor():
    def __init__(self):
        return True

if __name__ == '__main__':
    url = 'http://47.105.141.102:8889/group1/M00/00/00/rB8S22DDBx6ANSD0AA5watnx9X4002.pdf'
    pdf_parsor = pdf_parsor(url)
    path = pdf_parsor.download_file()
    pdf_parsor.pdf_parse(path)
