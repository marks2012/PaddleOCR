# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

__dir__ = os.path.dirname(__file__)
sys.path.append(os.path.join(__dir__, ''))

import cv2
import numpy as np
from pathlib import Path
import tarfile
import requests
from tqdm import tqdm

from tools.infer import predict_system
from ppocr.utils.logging import get_logger

logger = get_logger()
from ppocr.utils.utility import check_and_read_gif, get_image_file_list
from tools.infer.utility import draw_ocr

__all__ = ['PaddleOCR']

model_urls = {
    'det': {
        'ch':
        'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_det_infer.tar',
        'en':
        'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/en_ppocr_mobile_v2.0_det_infer.tar'
    },
    'rec': {
        'ch': {
            'url':
            'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_rec_infer.tar',
            'dict_path': './ppocr/utils/ppocr_keys_v1.txt'
        },
        'en': {
            'url':
            'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/en_number_mobile_v2.0_rec_infer.tar',
            'dict_path': './ppocr/utils/en_dict.txt'
        },
        'chinese_cht': {
            'url':
            'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/chinese_cht_mobile_v2.0_rec_infer.tar',
            'dict_path': './ppocr/utils/dict/chinese_cht_dict.txt'
        }
    },
    'cls':
    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar'
}

SUPPORT_DET_MODEL = ['DB']
VERSION = '2.1'
SUPPORT_REC_MODEL = ['CRNN']
BASE_DIR = os.path.expanduser("~/.paddleocr/")


def download_with_progressbar(url, save_path):
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(save_path, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes == 0 or progress_bar.n != total_size_in_bytes:
        logger.error("Something went wrong while downloading models")
        sys.exit(0)


def maybe_download(model_storage_directory, url):
    # using custom model
    tar_file_name_list = [
        'inference.pdiparams', 'inference.pdiparams.info', 'inference.pdmodel'
    ]
    if not os.path.exists(
            os.path.join(model_storage_directory, 'inference.pdiparams')
    ) or not os.path.exists(
            os.path.join(model_storage_directory, 'inference.pdmodel')):
        tmp_path = os.path.join(model_storage_directory, url.split('/')[-1])
        print('download {} to {}'.format(url, tmp_path))
        os.makedirs(model_storage_directory, exist_ok=True)
        download_with_progressbar(url, tmp_path)
        with tarfile.open(tmp_path, 'r') as tarObj:
            for member in tarObj.getmembers():
                filename = None
                for tar_file_name in tar_file_name_list:
                    if tar_file_name in member.name:
                        filename = tar_file_name
                if filename is None:
                    continue
                file = tarObj.extractfile(member)
                with open(
                        os.path.join(model_storage_directory, filename),
                        'wb') as f:
                    f.write(file.read())
        os.remove(tmp_path)


def parse_args():
    import argparse

    def str2bool(v):
        return v.lower() in ("true", "t", "1")

    parser = argparse.ArgumentParser()
    # params for prediction engine
    parser.add_argument("--use_gpu", type=str2bool, default=False)
    parser.add_argument("--ir_optim", type=str2bool, default=True)
    parser.add_argument("--use_tensorrt", type=str2bool, default=False)
    parser.add_argument("--gpu_mem", type=int, default=3000)

    # params for text detector
    parser.add_argument("--image_dir", type=str, default='./doc/imgs/')
    parser.add_argument("--det_algorithm", type=str, default='DB')
    parser.add_argument("--det_model_dir", type=str, default="./inference/ch_ppocr_server_v2.0_det_infer/")
    parser.add_argument("--det_limit_side_len", type=float, default=960)
    parser.add_argument("--det_limit_type", type=str, default='max')

    # DB parmas
    parser.add_argument("--det_db_thresh", type=float, default=0.3)
    parser.add_argument("--det_db_box_thresh", type=float, default=0.5)
    parser.add_argument("--det_db_unclip_ratio", type=float, default=1.6)
    parser.add_argument("--use_dilation", type=bool, default=False)
    parser.add_argument("--det_db_score_mode", type=str, default="fast")

    # EAST parmas
    parser.add_argument("--det_east_score_thresh", type=float, default=0.8)
    parser.add_argument("--det_east_cover_thresh", type=float, default=0.1)
    parser.add_argument("--det_east_nms_thresh", type=float, default=0.2)

    # params for text recognizer
    parser.add_argument("--rec_algorithm", type=str, default='CRNN')
    parser.add_argument("--rec_model_dir", type=str, default='./inference/ch_ppocr_server_v2.0_rec_infer/')
    parser.add_argument("--rec_image_shape", type=str, default="3, 32, 320")
    parser.add_argument("--rec_char_type", type=str, default='ch')
    parser.add_argument("--rec_batch_num", type=int, default=6)
    parser.add_argument("--max_text_length", type=int, default=25)
    parser.add_argument("--rec_char_dict_path", type=str, default=None)
    parser.add_argument("--use_space_char", type=bool, default=True)
    parser.add_argument("--drop_score", type=float, default=0.5)

    # params for text classifier
    parser.add_argument("--cls_model_dir", type=str, default="./inference/ch_ppocr_mobile_v2.0_cls_infer/")
    parser.add_argument("--cls_image_shape", type=str, default="3, 48, 192")
    parser.add_argument("--label_list", type=list, default=['0', '180'])
    parser.add_argument("--cls_batch_num", type=int, default=6)
    parser.add_argument("--cls_thresh", type=float, default=0.9)

    parser.add_argument("--enable_mkldnn", type=bool, default=False)
    parser.add_argument("--use_zero_copy_run", type=bool, default=False)
    parser.add_argument("--use_pdserving", type=str2bool, default=False)

    parser.add_argument("--lang", type=str, default='ch')
    parser.add_argument("--det", type=str2bool, default=True)
    parser.add_argument("--rec", type=str2bool, default=True)
    parser.add_argument("--use_angle_cls", type=str2bool, default=True)
    return parser.parse_args()


class PaddleOCR(predict_system.TextSystem):
    def __init__(self):
        """
        paddleocr package
        args:
            **kwargs: other params show in paddleocr --help
        """
        postprocess_params = parse_args()
        self.use_angle_cls = postprocess_params.use_angle_cls
        lang = postprocess_params.lang

        if lang == "ch":
            det_lang = "ch"
        else:
            det_lang = "en"
        use_inner_dict = False
        if postprocess_params.rec_char_dict_path is None:
            use_inner_dict = True
            postprocess_params.rec_char_dict_path = model_urls['rec'][lang][
                'dict_path']

        # init model dir
        if postprocess_params.det_model_dir is None:
            postprocess_params.det_model_dir = os.path.join(BASE_DIR, VERSION,
                                                            'det', det_lang)
        if postprocess_params.rec_model_dir is None:
            postprocess_params.rec_model_dir = os.path.join(BASE_DIR, VERSION,
                                                            'rec', lang)
        if postprocess_params.cls_model_dir is None:
            postprocess_params.cls_model_dir = os.path.join(BASE_DIR, 'cls')
        print(postprocess_params)
        # download model
        maybe_download(postprocess_params.det_model_dir,
                       model_urls['det'][det_lang])
        maybe_download(postprocess_params.rec_model_dir,
                       model_urls['rec'][lang]['url'])
        maybe_download(postprocess_params.cls_model_dir, model_urls['cls'])

        if postprocess_params.det_algorithm not in SUPPORT_DET_MODEL:
            logger.error('det_algorithm must in {}'.format(SUPPORT_DET_MODEL))
            sys.exit(0)
        if postprocess_params.rec_algorithm not in SUPPORT_REC_MODEL:
            logger.error('rec_algorithm must in {}'.format(SUPPORT_REC_MODEL))
            sys.exit(0)
        if use_inner_dict:
            postprocess_params.rec_char_dict_path = str(
                Path(__file__).parent / postprocess_params.rec_char_dict_path)

        # init det_model and rec_model
        super().__init__(postprocess_params)

    def ocr(self, img, det=True, rec=True, cls=False):
        """
        ocr with paddleocr
        args：
            img: img for ocr, support ndarray, img_path and list or ndarray
            det: use text detection or not, if false, only rec will be exec. default is True
            rec: use text recognition or not, if false, only det will be exec. default is True
        """
        if cls == False:
            self.use_angle_cls = False
        elif cls == True and self.use_angle_cls == False:
            logger.warning(
                'Since the angle classifier is not initialized, the angle classifier will not be uesd during the forward process'
            )

        if isinstance(img, str):
            # download net image
            if img.startswith('http'):
                download_with_progressbar(img, 'tmp.jpg')
                img = 'tmp.jpg'
            image_file = img
            img, flag = check_and_read_gif(image_file)
            if not flag:
                with open(image_file, 'rb') as f:
                    np_arr = np.frombuffer(f.read(), dtype=np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if isinstance(img, np.ndarray) and len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if det and rec:
            dt_boxes, rec_res = self.__call__(img, image_file)
            return [[box.tolist(), res] for box, res in zip(dt_boxes, rec_res)]
        elif det and not rec:
            dt_boxes, elapse = self.text_detector(img)
            if dt_boxes is None:
                return None
            return [box.tolist() for box in dt_boxes]
        else:
            if not isinstance(img, list):
                img = [img]
            if self.use_angle_cls:
                img, cls_res, elapse = self.text_classifier(img)
                if not rec:
                    return cls_res
            rec_res, elapse = self.text_recognizer(img)
            return rec_res


if __name__ == '__main__':
    # for cmd
    ocr_engine = PaddleOCR()

    path = './doc/pdf/temp/page-5.png'
    result = ocr_engine.ocr(path,
                            det=False,
                            rec=False,
                            cls=True)
