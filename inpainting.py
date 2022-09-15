import cv2
from PIL import Image
import os
import sys
import importlib
import numpy as np
from tqdm import tqdm

import torch
from torchvision.transforms import ToTensor

from util.option_inpaint import args


def main(args):
    args.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    clip = os.path.basename(args.src)
    args.imgdir = os.path.join(args.src,'images')
    args.maskdir = os.path.join(args.src,'masks')
    args.resultdir = os.path.join(args.dstdir,args.model,clip)
    os.makedirs(args.resultdir,exist_ok=True)
    
    flist = os.listdir(args.imgdir)
    flist.sort()
    
    if args.model == 'aotgan':
        def postprocess(image):
            image = torch.clamp(image, -1., 1.)
            image = (image + 1) / 2.0 * 255.0
            image = image.permute(1, 2, 0)
            image = image.cpu().numpy().astype(np.uint8)
            return image
        
        # AOT-GAN Model
        args.block_num = 8
        args.rates = [1,2,4,8]
        net = importlib.import_module('AOT-GAN-for-Inpainting.src.model.'+args.model)
        model = net.InpaintGenerator(args).to(args.device)
        model.load_state_dict(torch.load("AOT-GAN-for-Inpainting/experiments/G0000000.pt", map_location=args.device))
        model.eval()
        
        frames = [cv2.imread(os.path.join(args.imgdir,f),cv2.IMREAD_COLOR) for f in flist]
        masks = [cv2.imread(os.path.join(args.maskdir,f),cv2.IMREAD_GRAYSCALE) for f in flist]

        args.h,args.w,_ = frames[0].shape
        args.new_w = int(np.ceil(args.h * 16 / 9))
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        for i in tqdm(range(len(frames))):
            frame, mask, fname  = frames[i], masks[i], flist[i]
            img_tensor = (ToTensor()(frame) * 2.0 - 1.0).unsqueeze(0).to(args.device)
            mask = np.reshape(mask, (args.h,args.w,1))
            mask = cv2.dilate(mask,dilate_kernel,iterations=4)

            with torch.no_grad():
                mask_tensor = (ToTensor()(mask)).unsqueeze(0).to(args.device)
                masked_tensor = (img_tensor * (1 - mask_tensor).float()) + mask_tensor
                pred_tensor = model(masked_tensor, mask_tensor)
                comp_tensor = (pred_tensor * mask_tensor + img_tensor * (1 - mask_tensor))
                comp_np = postprocess(comp_tensor[0])
            cv2.imwrite(os.path.join(args.resultdir,fname), comp_np)
        print(f"Inpainted Images are stored in {args.resultdir}")
        print("Complete")
    else: # 'e2fgvi, e2fgvi_hq
        ref_length = 10  # ref_step
        num_ref = -1
        neighbor_stride = 5
        
        sys.path.append('./E2FGVI')
        to_tensors = importlib.import_module('core.utils').to_tensors
        
        def get_ref_index(f, neighbor_ids, length):
            ref_index = []
            if num_ref == -1:
                for i in range(0, length, ref_length):
                    if i not in neighbor_ids:
                        ref_index.append(i)
            else:
                start_idx = max(0, f - ref_length * (num_ref // 2))
                end_idx = min(length, f + ref_length * (num_ref // 2))
                for i in range(start_idx, end_idx + 1, ref_length):
                    if i not in neighbor_ids:
                        if len(ref_index) > num_ref:
                            break
                        ref_index.append(i)
            return ref_index

        # read frame-wise masks
        def read_mask(mlist, size):
            masks = []
            for mp in mlist:
                m = Image.open(mp)
                m = m.resize(size, Image.NEAREST)
                m = np.array(m.convert('L'))
                m = np.array(m > 0).astype(np.uint8)
                m = cv2.dilate(m,
                            cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)),
                            iterations=4)
                masks.append(Image.fromarray(m * 255))
            return masks

        #  read frames from video
        def read_frame_from_videos(flist):
            frames = []
            for fr in flist:
                image = cv2.imread(fr)
                image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                frames.append(image)
            return frames

        # resize frames
        def resize_frames(frames, size=None):
            if size is not None:
                frames = [f.resize(size) for f in frames]
            else:
                size = frames[0].size
            return frames, size

        if args.model == 'e2fgvi':
            size = (432, 240)
            args.ckpt = 'E2FGVI/release_model/E2FGVI-CVPR22.pth'
        else:
            args.ckpt = 'E2FGVI/release_model/E2FGVI-HQ-CVPR22.pth'
            size = None
            
        # E2FGVI Model
        net = importlib.import_module('model.' + args.model)
        model = net.InpaintGenerator().to(args.device)
        model.load_state_dict(torch.load(args.ckpt, map_location=args.device))
        model.eval()
        
        ilist = [os.path.join(args.imgdir,f) for f in flist]
        mlist = [os.path.join(args.maskdir,f) for f in flist]
        
        frames = read_frame_from_videos(ilist)
        frames, size = resize_frames(frames, size)
        h, w = size[1], size[0]
        video_length = len(frames)
        imgs = to_tensors()(frames).unsqueeze(0) * 2 - 1
        frames = [np.array(f).astype(np.uint8) for f in frames]
        masks = read_mask(mlist, size)
        binary_masks = [
            np.expand_dims((np.array(m) != 0).astype(np.uint8), 2) for m in masks
        ]
        masks = to_tensors()(masks).unsqueeze(0)
        # imgs, masks = imgs.to(args.device), masks.to(args.device)
        comp_frames = [None] * video_length
        
        for f in tqdm(range(0, video_length, neighbor_stride)):
            neighbor_ids = [
                i for i in range(max(0, f - neighbor_stride),
                                min(video_length, f + neighbor_stride + 1))
            ]
            ref_ids = get_ref_index(f, neighbor_ids, video_length)
            
            # 총 프레임 17개 넘어가면 현재 프레임에서 가장 먼 프레임 없애기
            # 이렇게 해야 12GB 이하인 VRAM에서 640x480 해상도 출력 가능
            for _ in range(max(0,len(ref_ids)+len(neighbor_ids) - 17)):
                if abs(f-ref_ids[0]) < abs(f-ref_ids[-1]):
                    ref_ids.pop()
                else:
                    ref_ids.pop(0)

            selected_imgs = imgs[:1, neighbor_ids + ref_ids, :, :, :]
            selected_masks = masks[:1, neighbor_ids + ref_ids, :, :, :]

            with torch.no_grad():
                masked_imgs = selected_imgs * (1 - selected_masks)
                masked_imgs = masked_imgs.to(args.device)
                mod_size_h = 60
                mod_size_w = 108
                h_pad = (mod_size_h - h % mod_size_h) % mod_size_h
                w_pad = (mod_size_w - w % mod_size_w) % mod_size_w
                masked_imgs = torch.cat(
                    [masked_imgs, torch.flip(masked_imgs, [3])],
                    3)[:, :, :, :h + h_pad, :]
                masked_imgs = torch.cat(
                    [masked_imgs, torch.flip(masked_imgs, [4])],
                    4)[:, :, :, :, :w + w_pad]
                pred_imgs, _ = model(masked_imgs, len(neighbor_ids))
                pred_imgs = pred_imgs[:, :, :h, :w]
                pred_imgs = (pred_imgs + 1) / 2
                pred_imgs = pred_imgs.cpu().permute(0, 2, 3, 1).numpy() * 255
                torch.cuda.empty_cache() # GPU 캐시를 정리해서 GPU 공간 확보
                for i in range(len(neighbor_ids)):
                    idx = neighbor_ids[i]
                    img = np.array(pred_imgs[i]).astype(
                        np.uint8) * binary_masks[idx] + frames[idx] * (
                            1 - binary_masks[idx])
                    if comp_frames[idx] is None:
                        comp_frames[idx] = img
                    else:
                        comp_frames[idx] = comp_frames[idx].astype(
                            np.float32) * 0.5 + img.astype(np.float32) * 0.5
        for f in range(video_length):
            comp = comp_frames[f].astype(np.uint8)
            cv2.imwrite(os.path.join(args.resultdir,flist[f]),cv2.cvtColor(comp, cv2.COLOR_BGR2RGB))
        print(f"Inpainted Images are stored in {args.resultdir}")
        print("Complete")

if __name__ == '__main__':
    main(args)