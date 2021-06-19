# -*- coding:UTF-8 -*-
# parse files, including ocr,
import os
import json

import cv2
import pandas as pd
import requests
import fitz
from PIL import Image

import utils
from paddleocr import PaddleOCR
from table.table_detect import table_detect

class pdf_parsor():
    def __init__(self, url):
        #self.file_id = file_id
        self.url = url

    # 对ocr解析结果进行行识别，并增加行item数
    def file_structs_rec(self, file_ocr_df):
        merged_df = pd.DataFrame()
        # 行汇总，把同一行的结果进行汇总
        new_line = True
        line = {}
        for item in file_ocr_df.iterrows():
            if new_line or item['pre_y_diff'] > 10:
                line['item_cnt'] = 1
                line['text'] = item['text']
                line['x1'] = item['x1']
                line['x2'] = item['x2']
                line['y1'] = item['y1']
                line['y2'] = item['y2']
            if item['pre_y_diff'] <= 10:
                line['item_cnt'] = line['item_cnt'] + 1
                line['text'] = line['text'] + '#i#' + item['text']
                line['x2'] = item['x2']
                line['y2'] = item['y2']

        return file_ocr_df

    # 基于ocr结果进行文件整体逻辑提取，包括如下功能：
    # 1. 标题，段落识别
    # 2. 页眉，页尾识别
    # 3. 表格识别
    def file_structs_rec(self, file_ocr_df):
        df = pd.DataFrame()
        # 行汇总，把同一行的结果进行汇总
        line_item_cnt = 0

        for item in file_ocr_df.iterrows():
            print('abc')

        return file_ocr_df

    # ocr结果转换成dataframe，并计算部分通用标签
    def ocr_2_df(self, ocr_result):
        ocr_df = pd.DataFrame()
        if len(ocr_result):
            ocr_df['x1'] = pd.Series([item[0][0][0] for item in ocr_result])
            ocr_df['x2'] = pd.Series([item[0][1][0] for item in ocr_result])
            ocr_df['y1'] = pd.Series([item[0][0][1] for item in ocr_result])
            ocr_df['y2'] = pd.Series([item[0][1][1] for item in ocr_result])
            ocr_df['text'] = pd.Series([item[1][0] for item in ocr_result])
            ocr_df['score'] = pd.Series([item[1][1] for item in ocr_result])
            ocr_df['lenth'] = ocr_df['x2'] - ocr_df['x1']
            ocr_df['height'] = ocr_df['y2'] - ocr_df['y1']

            # 计算相邻两个文本之间的x轴间隔
            next_x1 = ocr_df['x1'].copy()
            next_x1.index = next_x1.index - 1
            next_x1.drop(index=-1, inplace=False)
            ocr_df['next_x_diff'] = next_x1 - ocr_df['x2']
            # 计算相邻两个文本之间的y轴间隔
            next_y1 = ocr_df['y1'].copy()
            next_y1.index = next_y1.index - 1
            next_y1.drop(index=-1, inplace=False)
            ocr_df['next_y_diff'] = next_y1 - ocr_df['y2']

        return ocr_df

    # 解析pdf文件，完成如下任务：
    # 1. 基于pymupdf直接解析pdf，获取其中文字，图片等内容
    # 2. 基于ocr对pdf进行解析，首先保存每一页的pdf图片并对图片进行初步判断（旋转等）
    # 2.1 对图片中提取的文字进行分析，判断标题，段落等信息（基于位置内容和正则表达式）
    # 2.2 对图片中表格进行检测，并基于OCR结果对表格进行重构，包括表格名称等
    # 2.3 对页眉页尾进行识别
    # 2.4 对目录页进行识别
    def parse(self):
        root = './doc/pdf/'
        # 下载文件并生成对应的文件夹
        file_dir, file_path = utils.download_file(self.url, root)
        # 子文件夹
        img_dir = file_dir + 'img/'
        ocr_dir = file_dir + 'ocr/'
        excel_dir = file_dir + 'excel/'
        # 针对每个页面生成子文件，存放当前页面提取出来的文本，图片，excel等
        try:
            if not os.path.exists(img_dir):
                os.mkdir(img_dir)
            if not os.path.exists(ocr_dir):
                os.mkdir(ocr_dir)
            if not os.path.exists(excel_dir):
                os.mkdir(excel_dir)
        except:
            print("create page dirs failed.")

        # 开始解析
        self.doc = fitz.open(file_path)
        self.ocr_engine = PaddleOCR()
        self.file_ocr_df = pd.DataFrame()
        for page in self.doc:
            print('Process page: %s'%page.number)
            # 获取直接提取的文本
            page_text = page.get_text("text")
            print('text: %s'%page_text)

            # 获取页面图片并保存到本地
            pix = page.get_pixmap()
            page_img_path = img_dir + "page_%s.png" % str(1000 + page.number)[1:]
            pix.save(page_img_path)

            # 对page img做OCR解析
            # 如果文本检测boxes中竖长方形较多，则对图像进行翻转，后续结合文字角度进行综合判断
            page_ocr_result = self.ocr_engine.ocr(page_img_path)

            # 表格检测
            # boxes, adBoxes, scores = table_detect(cv2.imread(page_img_path), sc=(416, 416), thresh=0.5, NMSthresh=0.3)
            # if len(boxes):
            #     print(boxes)

            # ocr解析结果转为dataframe并保存
            page_ocr_df = self.ocr_2_df(page_ocr_result)
            page_ocr_df['page_no'] = page.number
            # page_ocr_df_json = page_ocr_df.to_json(force_ascii = False)
            page_ocr_df.to_excel(ocr_dir + "page_%s.xlsx" % str(1000 + page.number)[1:], encoding = 'utf-8')
            self.file_ocr_df = self.file_ocr_df.append(page_ocr_df)

            # 识别页面中是否包含表格

            # 保存ocr解析结果中的纯文本内容
            page_ocr_text = utils.ocr_2_text(page_ocr_result)
            print('ocr_text: %s' % page_ocr_text)

            paragraph = page.get_text("blocks")
            print('blocks:%s'%paragraph)

            words = page.get_text("words")
            print('words:%s' % words)

        # 整个文件的解析结果
        self.file_structs_rec(self.file_ocr_df)
        self.file_ocr_df.to_excel(file_dir + '/ocr_result.xlsx', encoding = 'utf-8')
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
    # path = pdf_parsor.download_file()
    path = './doc/pdf/temp/rB8S22DDBx6ANSD0AA5watnx9X4002.pdf'
    pdf_parsor = pdf_parsor(url)
    pdf_parsor.parse()
