import argparse
import os
from pathlib import Path
from pdb import set_trace as bp

import cv2
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

import models.modules.Sakuya_arch as Sakuya_arch
from data.util import imresize_np

parser = argparse.ArgumentParser()
parser.add_argument('--space_scale', type=int, default=4, help="upsampling space scale")
parser.add_argument('--downsample', type=bool, default=False, help="whether to downsample input frames by space_scale")
parser.add_argument('--time_scale', type=int, default=8, help="upsampling time scale")
parser.add_argument('--data_path', type=str, required=True, help="data path for testing")
parser.add_argument('--out_path', type=str, default="./demo_output/", help="output path (with subdirs for BC, LR and VideoINR)")
parser.add_argument('--model_path', type=str, default="latest_G.pth", help="model parameter path")
opt = parser.parse_known_args()[0]

device = 'cuda'
model = Sakuya_arch.LunaTokis(64, 6, 8, 5, 40)
model.load_state_dict(torch.load(opt.model_path), strict=True)

model.eval()
model = model.to(device)

def single_forward(model, imgs_in, space_scale, time_scale):
    with torch.no_grad():
        b, n, c, h, w = imgs_in.size()
        h_n = int(4 * np.ceil(h / 4))
        w_n = int(4 * np.ceil(w / 4))
        imgs_temp = imgs_in.new_zeros(b, n, c, h_n, w_n)
        imgs_temp[:, :, :, 0:h, 0:w] = imgs_in

        time_Tensors = [torch.tensor([i / time_scale])[None].to(device) for i in range(time_scale)]
        model_output = model(imgs_temp, time_Tensors, space_scale, test=True)
        return model_output

path_LR = Path(opt.out_path).joinpath("LR")
path_BC = Path(opt.out_path).joinpath("Bicubic")
path_VideoINR = Path(opt.out_path).joinpath("VideoINR")
os.makedirs(path_LR, exist_ok=True)
os.makedirs(path_BC, exist_ok=True)
os.makedirs(path_VideoINR, exist_ok=True)

# correctly sort input videos by number, should work for "001" and "1" formats
path_list = list(Path(opt.data_path).iterdir())
filestem_list = np.array([f.stem for f in path_list], int)
sort_idx = filestem_list.argsort()
path_list = np.array(list(path_list), str)[sort_idx]

index = 0
for idx in tqdm(range(len(path_list) - 1)):

    imgpath1 = path_list[idx]
    imgpath2 = path_list[idx + 1]

    img1 = cv2.imread(imgpath1, cv2.IMREAD_UNCHANGED)
    img2 = cv2.imread(imgpath2, cv2.IMREAD_UNCHANGED)

    if opt.downsample:
        # We apply down-sampling on the original vide in order to avoid CUDA
        # out of memory. You may skip this step if your input video is already
        # of relatively low resolution.
        #NOTE: check if intended to normalise RGB by 255
        img1 = imresize_np(img1, 1 / opt.space_scale, True).astype(np.float32) / 255.
        img2 = imresize_np(img2, 1 / opt.space_scale, True).astype(np.float32) / 255.

        # save LR from img1
        imgLR = Image.fromarray((np.clip(img1[:, :, [2, 1, 0]], 0, 1) * 255).astype(np.uint8))
        imgLR.save(path_LR.joinpath(os.path.basename(imgpath1)))

    # concat imgs
    imgs = np.stack([img1, img2], axis=0)[:, :, :, [2, 1, 0]]
    imgs = torch.from_numpy(np.ascontiguousarray(np.transpose(imgs, (0, 3, 1, 2)))).float()[None].to(device)

    # forward pass through model
    output = single_forward(model, imgs, opt.space_scale, opt.time_scale)

    # Save results of VideoINR and bicubic up-sampling.
    for out_ind in range(len(output)):
        img = output[out_ind][0]
        img = Image.fromarray((img.clamp(0., 1.).detach().cpu().permute(1, 2, 0) * 255).numpy().astype(np.uint8))
        img.save(path_VideoINR.joinpath("{}.png".format(index)))

        HH, WW = img1.shape[0] * 4, img1.shape[1] * 4
        imgBC = Image.fromarray((np.clip(img1[:, :, [2, 1, 0]], 0, 1) * 255).astype(np.uint8)).resize((WW, HH),Image.BICUBIC)
        imgBC.save(path_BC.joinpath("{}.png".format(index)))
        index += 1
