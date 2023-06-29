import cv2
import numpy as np
from PIL import Image
import glob
import cv2
import os
import shutil
from pathlib import Path
from pdb import set_trace as bp

# CONFIG - A hardcoded path here as an example
videoFolder = Path(r'adobe240\original_high_fps_videos')
frameFolder = Path(r'adobe240\frame')

train_txt = Path(r'data\adobe240fps_folder_train.txt')
valid_txt = Path(r'data\adobe240fps_folder_valid.txt')
test_txt = Path(r'data\adobe240fps_folder_test.txt')

# RUN
# TODO: make this script a function or runable from shell

with open(train_txt) as f:
    temp = f.readlines()
    train_list = [v.strip() for v in temp]

with open(valid_txt) as f:
    temp = f.readlines()
    valid_list = [v.strip() for v in temp]

with open(test_txt) as f:
    temp = f.readlines()
    test_list = [v.strip() for v in temp]

mov_files = videoFolder.glob('*')

def check_if_folder_exist(folder_path='/home/ubuntu/'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        if not os.path.isdir(folder_path):
            print('Folder: ' + folder_path + ' exists and is not a folder!')
            exit()

name_list = []
for i, mov_path in enumerate(mov_files):
    mov_name = mov_path.stem
    print(f"Converting file {i}:", mov_name)
    if mov_name in valid_list:
        mov_folder = frameFolder.joinpath('valid')
    elif mov_name in test_list:
        mov_folder = frameFolder.joinpath('test')
    elif mov_name in train_list:
        mov_folder = frameFolder.joinpath('train')
    else:
        print(f"File not on any list: {mov_path}")
    
    image_index = 0
    video = cv2.VideoCapture(str(mov_path))
    success, frame = video.read()
    frame = np.transpose(frame, (0, 1, 2))
    while success:
        save_folder = mov_folder.joinpath(mov_name)
        check_if_folder_exist(save_folder)
        cv2.imwrite(str(save_folder.joinpath(str(image_index) + '.png')), frame)
        # print(str(i) + ' ' + str(image_index))
        image_index += 1
        success, frame = video.read()
        if not success:
            break
        frame = np.transpose(frame, (0, 1, 2))
