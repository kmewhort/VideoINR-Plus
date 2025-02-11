'''
Adobe240 dataset (constant downsample ratio)
support reading images from lmdb, image folder and memcached
'''
import logging
import os
import os.path as osp
import pickle
import random
import sys
from pathlib import Path

import cv2
import lmdb
import numpy as np
import torch
import torch.utils.data as data

import data.util as util

try:
    import mc  # import memcached
except ImportError:
    pass
from pdb import set_trace as bp

try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.util import imresize_np
except ImportError:
    pass

logger = logging.getLogger('base')


class AdobeDataset(data.Dataset):
    '''
    Reading the training Vimeo dataset
    key example: train/00001/0001/im1.png
    GT: Ground-Truth;
    LQ: Low-Quality, e.g., low-resolution frames
    support reading N HR frames, N = 3, 5, 7
    '''

    def __init__(self, opt):
        super(AdobeDataset, self).__init__()
        self.opt = opt
        # temporal augmentation
        self.interval_list = opt['interval_list']
        self.random_reverse = opt['random_reverse']
        logger.info(
            'Temporal augmentation interval list: [{}], with random reverse is {}.'.format(
                ','.join(str(x) for x in opt['interval_list']), self.random_reverse)
        )
        self.half_N_frames = opt['N_frames'] // 2
        self.LR_N_frames = 1 + self.half_N_frames
        assert self.LR_N_frames > 1, 'Error: Not enough LR frames to interpolate'
        #### determine the LQ frame list
        '''
        N | frames
        1 | error
        3 | 0,2
        5 | 0,2,4
        7 | 0,2,4,6
        '''
        self.LR_idx_list = []
        for i in range(self.LR_N_frames):
            self.LR_idx_list.append(i*2)

        self.GT_root, self.LQ_root = opt['dataroot_GT'], opt['dataroot_LQ']
        # automatically create LQ frames if GT and LQ roots are equal
        self.auto_downsample = (self.GT_root == self.LQ_root)
        self.data_type = self.opt['data_type']
        # low resolution inputs
        self.LR_input = False if opt['GT_size'] == opt['LQ_size'] else True
        #### directly load image keys
        if opt['cache_keys']:
            logger.info('Using cache keys: {}'.format(opt['cache_keys']))
            cache_keys = opt['cache_keys']
        else:
            cache_keys = 'Vimeo7_train_keys.pkl'
        logger.info('Using cache keys - {}.'.format(cache_keys))
        self.paths_GT = pickle.load(open('meta_info/{}'.format(cache_keys), 'rb'))

        assert self.paths_GT, 'Error: GT path is empty.'

        if self.data_type == 'lmdb':
            self.GT_env, self.LQ_env = None, None
        elif self.data_type == 'mc':  # memcached
            self.mclient = None
        elif self.data_type == 'img':
            pass
        else:
            raise ValueError('Wrong data type: {}'.format(self.data_type))

        # list of names of train videos
        with open('data/adobe240fps_folder_train.txt') as t:
            video_list = t.read().splitlines() # '\n' stripped automatically

        # list of filepath tuples
        self.lq_list = []  # each tuple contains 2 input frames
        self.gt_list = []  # each tuple contains all 9 consective frames
        interval = 8  # distance between input frames
        for video in video_list:
            # frame filename list for GT (should be identical to LQ)
            frame_dir = Path(self.GT_root, video)
            # get filenames with video dir, eg 'IMG_0000/0000.png'
            frames = [Path(video, f.name) for f in frame_dir.iterdir()]
            for idx in range(len(frames) - interval):
                idx_end = idx + interval  # for end input frame

                # get filepaths for frames i and i+8 (the 2 input frames)
                inputs_idx = [idx, idx_end]
                inputsLQ = [Path(self.LQ_root, frames[i]) for i in inputs_idx]
                self.lq_list.append(inputsLQ)

                # get filepaths for all frames i to i+8 (the 9 GT frames)
                frames_idx = range(idx, idx_end + 1)
                framesGT = [Path(self.GT_root, frames[i]) for i in frames_idx]
                self.gt_list.append(framesGT)

        print(len(self.lq_list))
        print(len(self.gt_list))


    def _init_lmdb(self):
        # https://github.com/chainer/chainermn/issues/129
        self.GT_env = lmdb.open(
            self.opt['dataroot_GT'],
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False,
        )
        self.LQ_env = lmdb.open(
            self.opt['dataroot_LQ'],
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False,
        )

    def _ensure_memcached(self):
        if self.mclient is None:
            # specify the config files
            server_list_config_file = None
            client_config_file = None
            self.mclient = mc.MemcachedClient.GetInstance(
                server_list_config_file, client_config_file
            )

    def _read_img_mc(self, path):
        ''' Return BGR, HWC, [0, 255], uint8'''
        value = mc.pyvector()
        self.mclient.Get(path, value)
        value_buf = mc.ConvertBuffer(value)
        img_array = np.frombuffer(value_buf, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        return img

    def _read_img_mc_BGR(self, path, name_a, name_b):
        ''' Read BGR channels separately and then combine for 1M limits in cluster'''
        img_B = self._read_img_mc(osp.join(path + '_B', name_a, name_b + '.png'))
        img_G = self._read_img_mc(osp.join(path + '_G', name_a, name_b + '.png'))
        img_R = self._read_img_mc(osp.join(path + '_R', name_a, name_b + '.png'))
        img = cv2.merge((img_B, img_G, img_R))
        return img

    def __getitem__(self, idx):
        scale = self.opt['scale']
        #NOTE: auto_s_f == (scale or 1) for self.auto_ds == (True or False)
        auto_scale_factor = scale ** self.auto_downsample
        GT_size = self.opt['GT_size']
        key = self.paths_GT[0]

        #### get the GT & LQ images (as the center frame)
        #### op == original_path; fp == file_path, l == list
        img_LQop_l = self.lq_list[idx]
        img_GTop_l = np.array(self.gt_list[idx])

        gt_sampled_idx = sorted(random.sample(range(len(img_GTop_l)), 1))
        # print(gt_sampled_idx)
        # gt_sampled_idx = [0, 4, 8]
        img_GTop_l = img_GTop_l[gt_sampled_idx]

        times = []
        for i in gt_sampled_idx:
            times.append(torch.tensor([i / 8]))

        # read frames
        img_LQ_l = [cv2.imread(str(fp)) for fp in img_LQop_l]
        img_GT_l = [cv2.imread(str(fp)) for fp in img_GTop_l]

        # crop so frames are divisible by scale factor (remove remainder)
        sf_l, sf_g = (2 * auto_scale_factor, 2)  # LQ, GT scale factors
        height_l, width_l = sf_l * (np.array(img_LQ_l[0].shape) // sf_l)[0:2]
        height_g, width_g = sf_g * (np.array(img_GT_l[0].shape) // sf_g)[0:2]
        if len(img_LQ_l[0].shape) == 3:
            img_LQ_l = [img_[0:height_l, 0:width_l, :] for img_ in img_LQ_l]
            img_GT_l = [img_[0:height_g, 0:width_g, :] for img_ in img_GT_l]
        else:
            img_LQ_l = [img_[0:height_l, 0:width_l] for img_ in img_LQ_l]
            img_GT_l = [img_[0:height_g, 0:width_g] for img_ in img_GT_l]

        # downsample images by half
        img_LQ_l = [imresize_np(img_, 1 / sf_l, True) for img_ in img_LQ_l]
        img_GT_l = [imresize_np(img_, 1 / sf_g, True) for img_ in img_GT_l]

        # convert to float RBG
        img_LQ_l = [img_.astype(np.float32) / 255.0 for img_ in img_LQ_l]
        img_GT_l = [img_.astype(np.float32) / 255.0 for img_ in img_GT_l]

        # format array dimensions
        if img_LQ_l[0].ndim == 2:
            img_LQ_l = [np.expand_dims(img_, axis=2) for img_ in img_LQ_l]
            img_GT_l = [np.expand_dims(img_, axis=2) for img_ in img_GT_l]

        if img_LQ_l[0].shape[2] > 3:
            img_LQ_l = [img_[:, :, :3] for img_ in img_LQ_l]
            img_GT_l = [img_[:, :, :3] for img_ in img_GT_l]

        H, W, C = img_LQ_l[0].shape[0:3]
        if self.opt['phase'] == 'train':
            # randomly crop
            if self.LR_input:
                LQ_size = GT_size // scale
                # random starting corner for crop
                rnd_h = random.randint(0, max(0, H - LQ_size))
                rnd_w = random.randint(0, max(0, W - LQ_size))
                img_LQ_l = [v[rnd_h:rnd_h + LQ_size, rnd_w:rnd_w + LQ_size, :] for v in img_LQ_l]
                rnd_h_HR, rnd_w_HR = int(rnd_h * scale), int(rnd_w * scale)
                img_GT_l = [v[rnd_h_HR:rnd_h_HR + GT_size, rnd_w_HR:rnd_w_HR + GT_size, :] for v in img_GT_l]
            else:
                rnd_h = random.randint(0, max(0, H - GT_size))
                rnd_w = random.randint(0, max(0, W - GT_size))
                img_LQ_l = [v[rnd_h:rnd_h + GT_size, rnd_w:rnd_w + GT_size, :] for v in img_LQ_l]
                img_GT_l = [v[rnd_h:rnd_h + GT_size, rnd_w:rnd_w + GT_size, :] for v in img_GT_l]

            # augmentation - flip, rotate
            img_LQ_l = img_LQ_l + img_GT_l
            rlt = util.augment(img_LQ_l, self.opt['use_flip'], self.opt['use_rot'])
            img_LQ_l = rlt[0:2]
            img_GT_l = rlt[2:]

        # stack LQ images to NHWC, N is the frame number
        img_LQs = np.stack(img_LQ_l, axis=0)
        img_GTs = np.stack(img_GT_l, axis=0)
        # BGR to RGB, HWC to CHW, numpy to tensor
        img_GTs = img_GTs[:, :, :, [2, 1, 0]]
        img_LQs = img_LQs[:, :, :, [2, 1, 0]]

        img_GTs = torch.from_numpy(
            np.ascontiguousarray(np.transpose(img_GTs, (0, 3, 1, 2)))
        ).float()
        img_LQs = torch.from_numpy(
            np.ascontiguousarray(np.transpose(img_LQs, (0, 3, 1, 2)))
        ).float()

        return {
            'LQs': img_LQs,
            'GT': img_GTs,
            'key': key,
            'time': times,
            'scale': (img_GTs.shape[-2], img_GTs.shape[-1])
        }

    def __len__(self):
        return len(self.lq_list)
