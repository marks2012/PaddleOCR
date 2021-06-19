# -*- coding:UTF-8 -*-
import os.path

import pandas as pd
import cv2
import requests

def check_rotate(dt_boxes_df):
    check_df = dt_boxes_df.copy()
    # 如果竖立长方形数量超过一半则认为需要旋转图片
    check_df = check_df[check_df['length'] + check_df['hight'] > 50]
    if len(check_df[check_df['hight'] > check_df['length']]) > len(check_df) / 5 or len(check_df[check_df['hight'] > check_df['length']]) >= 3:
        return True
    return False

# box转为df
def box_to_df(dt_boxes):
    dt_boxes_df = pd.DataFrame()
    dt_boxes_df['x1'] = pd.Series(dt_boxes[:, 0, 0])
    dt_boxes_df['x2'] = pd.Series(dt_boxes[:, 1, 0])
    dt_boxes_df['x3'] = pd.Series(dt_boxes[:, 2, 0])
    dt_boxes_df['x4'] = pd.Series(dt_boxes[:, 3, 0])
    dt_boxes_df['y1'] = pd.Series(dt_boxes[:, 0, 1])
    dt_boxes_df['y2'] = pd.Series(dt_boxes[:, 1, 1])
    dt_boxes_df['y3'] = pd.Series(dt_boxes[:, 2, 1])
    dt_boxes_df['y4'] = pd.Series(dt_boxes[:, 3, 1])
    dt_boxes_df['length'] = dt_boxes_df['x3'] - dt_boxes_df['x1']
    dt_boxes_df['hight'] = dt_boxes_df['y3'] - dt_boxes_df['y1']

    return dt_boxes_df

# 在原图上面添加文字检测的框
def img_add_box(img, dt_boxes):
    for box in dt_boxes:
        box = box.astype(int)
        cv2.rectangle(img, tuple(box[0]), tuple(box[2]), (0, 255, 0), 2)
    return img

# ocr文本结果处理：拼成整个文本
def ocr_2_text(ocr_result):
    text = ''
    if len(ocr_result):
        text = '#line#'.join([line[1][0] for line in ocr_result])
    return text

# ocr结果转换成dataframe，并计算部分通用标签
def ocr_2_df(ocr_result):
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


# ocr文本检测结果处理：生成excel表格

# 下载文件到本地
def download_file(url, root):
    r = requests.get(url)
    file_name = url.split('/')[-1]
    dir_name = file_name.split('.')[0]
    file_dir = root + dir_name + '/'
    if not os.path.exists(root + dir_name):
        os.mkdir(root + dir_name)
    with open(root + dir_name + '/' + file_name, "wb") as code:
        code.write(r.content)
    return file_dir, file_dir + file_name