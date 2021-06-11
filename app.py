# -*- coding:UTF-8 -*-
# Model Service entry
# Support different biz scenarios:
# 1. pdf parse, for each page:
#    a. extract text and excel from pdf. If text length less than 100, try ocr
#    b. extract img from pdf, save it and upload to file server
# 2. word parse:
# 3. excel parse:
# save the parse result to elastic search and db tables.

from flask import Flask, request, make_response
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
import requests
import multiprocessing
import pandas as pd
from configparser import ConfigParser
import os
import datetime

app = Flask(__name__)

config = ConfigParser().read('config.ini', encoding='utf-8')
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

def parse_file(file_id, url):
    '''
    解析文件，基于文件类型调用不同的解析方案，包括pdf解析，word解析，excel解析。
    解析结果包括：文件内容（json格式，包括文本，表格，图片等），文件表格，文件文本
    '''
    return True

@app.route('/')
def hello():
    return "hello"

@app.route('/runModel', methods=['POST'])
def run_model():
    request_data = request.get_data()
    try:
        context = json.loads(request_data, encodings='utf-8', strict=False)
        model_name = context['model_name']
        file_id = context['file_id']
        url = context['url']

        logger.info("%s: start to run model %s"%(datetime.datetime.now(), context['model_name']))
        # 异步处理：run model in another process
        if model_name == 'ocr':
            # 对文件进行处理，基于文件ID和文件URL获取文件内容，并把解析后的结果保存到es以及mysql库
            parse_file(file_id, url)
            print("调用OCR对文件进行解析")
        elif model_name == 'extract':
            print("对文档内容进行提取")

        response = make_response("Success", 200)
    except Exception as e:
        logger.exception(e)
        return make_response("Failed to run model.", 500)
    return response


@app.route('/startModelInstance', methods=['POST'])
def start_model_instance():
    request_data = request.get_data()
    response = make_response()
    return response

if __name__ == '__main__':
    logger.info("%s: Starting server..."%datetime.datetime.now())
    app.run(host='0.0.0.0', port='8080')
