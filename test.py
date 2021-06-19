import numpy as np
import cv2
from paddleocr import PaddleOCR
import utils

image_file = 'D:\\work\\pycharm\\doc_parsing\\doc\\pdf\\rB8S22DDBx6ANSD0AA5watnx9X4002\\img\\page_010.png'

img = cv2.imread(image_file)
ocr_engine = PaddleOCR()

dt_boxes, elapse = ocr_engine.text_detector(img)
# 首先把dt_boxes转换为dataframe
dt_boxes_df = utils.box_to_df(dt_boxes)
# 检查是否需要旋转：如果dt_boxes大都为竖立长方形，则大概率需要旋转
need_rotate = utils.check_rotate(dt_boxes_df)

img = utils.img_add_box(img, dt_boxes)

cv2.imwrite(image_file, img)

# img2_rotate = np.rot90(img, axes=(1,0))
# cv2.imwrite('./doc/pdf/temp/page-5-1.png', img2_rotate)