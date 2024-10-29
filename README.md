# Updated ORPVR Installation and Usage Guide
Hi as you all know the original ORPVR by https://github.com/jinjungyu/ORPVR has been outdated and does not have any version checking so this repo will help to find and explain the required libraries (and versions) especially those facing issues with mmcv and mmdet

##### Research paper:
##### J. -G. Jin, J. Bae, H. -G. Baek and S. -H. Park, "Object-Ratio-Preserving Video Retargeting Framework based on Segmentation and Inpainting," 2023 IEEE/CVF Winter Conference on Applications of Computer Vision Workshops (WACVW), Waikoloa,HI, USA, 2023, pp. 497-503, doi: 10.1109/WACVW58289.2023.00055.

## Notes/Precautions:
#### After hours of finding the correct version, I discovered these key changes and important precautions to take when installing:
1. You cannot use `mmcv>=2.0.0` as the new configuration lacks the appropriate models and dependencies that are needed for ORPVR
2. Do not install `mmdet` independently as it will also force install the later or compatible version of mmcv 
3. You have to `pip install -v -e .` from the mmdetection 2.x, as I will explain later
4. Tensorflow does not have support for the later cuda versions (12.x), so it is best to install (11.x)
5. Missing dll files can be identified and downloaded
6. Crop step was missing from the repo, so I added `crop.py` to crop the images from DAVIS 2016 as mentioned in their paper before running the pipeline: 
    - Original repo: masking->inpainting->relocating->encoding
    - This repo: crop->masking->inpainting->relocating->encoding
7. AOT-GAN has a poorer performance as mentioned in the paper, but it can be selected and used.
8. If you are using GPU, install the relvant python GPU torch libraries (Step 1 in Setting up Guide) BEFORE installing mmcv-full, or else you will install the mmcv-full CPU version.

Video Output:

https://github.com/user-attachments/assets/ba2d2ad6-ed55-43d9-bd63-faac7083846a


### Setting Up Guide
I use windows using python 3.9.x, but you can also set up a docker container if it is more manageable. Also, if you are using GPU. Remember to do step 1 first then step 2.
1. **Install the correct CUDA version (I am using 11.7)**
    ### CUDAv11.7
    - CUDA https://developer.nvidia.com/cuda-toolkit
    - check your CUDA_PATH using something like echo %CUDA_PATH% or if you are using windows like me, check using edit the system environment variables -> Advanced -> Environment Variables and then you should see:

    ![Screenshot 2024-09-21 231625](https://github.com/user-attachments/assets/26b4d499-afd6-4c33-b2c2-fd7a6d5160fd)
    under system variables, if not add a new CUDA_PATH and CUDA_PATH_V11_7 
    - Create a new conda environment (python 3.9.x)
    ```bash
    conda create -n SAM-ORPVR python=3.9
    ```
    
    - (For windows): If you are unable to switch the CUDA environment freely or see the conda version `(SAM-ORPVR) PS C:\Users\User...>`, run the following command below as `administrator`
    ```bash
    Set-ExecutionPolicy RemoteSigned
    ```
    
    - Activate the new environment
    ```bash
    conda activate SAM-ORPVR
    ```

    - Install correct python torch CUDA-enabled libraries for CUDA, run the commands here: (https://pytorch.org/get-started/previous-versions/)
    ```bash
    conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia
    ```

    - ^ if the above does not work and you still get a CUDA error run
    ```bash
    pip uninstall torch torchvision torchaudio
    ```
    then
    ```bash
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
    ```

    - after installing tensorflow and CUDA-enabled torch, you should get these versions:
    ```bash
    torch                         2.0.1+cu117
    torchaudio                    2.0.2+cu117
    torchvision                   0.15.2+cu117
    ```

    run the following code to check cuda:
    ```bash
    python cudacheck.py
    ```
    
    you should get this:
    ```bash
    torch GPU check:
    True
    GPU:NVIDIA GeForce RTX 3070
    ```

    - then add in the appropriate dll files if not found (for me it was cudnn64_8.dll not found):
    https://www.dll-files.com/cudnn64_8.dll.html#google_vignette
    place it in the
    NVIDIA GPU Computing Toolkit\CUDA\v11.7\bin

    check CUDA using this command:
    ```bash
    nvcc --version
    ```

    You should get:
    ```bash
    nvcc: NVIDIA (R) Cuda compiler driver
    Copyright (c) 2005-2022 NVIDIA Corporation
    Built on Tue_May__3_19:00:59_Pacific_Daylight_Time_2022
    Cuda compilation tools, release 11.7, V11.7.64
    Build cuda_11.7.r11.7/compiler.31294372_0
    ```
    - download `util` file in `test clear` commit of main branch (ORPVR SHA eef6dcb39e05041e044e46141db80d37fb93d9b4)
      https://github.com/jinjungyu/ORPVR/tree/main (I included here so you dont have to)

    ### CPU only
    - If you want the cpu version only then do:
    ```bash
     pip install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0
    ```

2. **Install Dependencies and DAVIS 2016 dataset (Order is important, FOLLOW carefully):**
    - Install openmim
    ```bash
    pip install -U openmim
    mim install mmcv-full
    ```

    - Davis Dataset: https://davischallenge.org/davis2016/code.html

    - Download mmdetection v2.0
    https://github.com/open-mmlab/mmdetection/tree/2.x

    ```bash
    cd mmdetection
    mkdir checkpoints
    pip install -v -e .
    ```
    *WARNING: DO NOT install mmcv==1.7.2 and the latest version (2.0.0+) as it will lead to keyErrors mmcv.runner and mmcv._ext module not found

    Ensure you have the following versions of the packages:
   - `mmcv-full` 1.7.2
   - `mmdet` 2.28.2
   - `mmengine` 0.10.4

   *If you accidentally install the wrong version (probably if you install mmdetection 3.x+), uninstall the current packages and reinstall:

    ```bash
    pip uninstall mmdet
    pip uninstall mmcv
    pip uninstall mmcv-full
    pip install -U openmim
    mim install mmcv-full

    cd mmdetection
    mkdir checkpoints
    pip install -v -e .
    ```
    then make sure you are using mmdetection v2.0:
    https://github.com/open-mmlab/mmdetection/tree/2.x
    before running 
    
    ```bash
    cd mmdetection
    mkdir checkpoints
    pip install -v -e .
    ```
    again

    then install the necessary libraries:
    ```bash
    pip install -r requirements.txt
    ```


3. **mask2former Model**
    - Download mask2former model and put inside `mmdetection/checkpoints` (branch 2.0): https://github.com/open-mmlab/mmdetection/blob/2.x/configs/mask2former/README.md

4. **SAM Model**:
    ```bash
    mkdir SAM
    cd SAM
    mkdir checkpoints
    ```
    - Install segment anything

    ```bash
    pip install git+https://github.com/facebookresearch/segment-anything.git
    ```

    - Download SAM model and put inside `SAM/checkpoints` : https://github.com/facebookresearch/segment-anything?tab=readme-ov-file#model-checkpoints
    *I am using `vit_h`, options are `vit_h`,`vit_l`,`vit_b`
    Note: Requires device spec

    SAM2:
    * Install SAM2
    ```bash
    git clone https://github.com/facebookresearch/sam2.git
    cd sam2
    ```

    * Also, we use python `3.9.x` here because it works with E2FGVI and mask2former (the previous set up), the 3.10.x suggested by Meta is only for accelerated computing
    https://github.com/facebookresearch/sam2/blob/main/INSTALL.md

    * The error below occurs if you dont have desktop environment for C++ installed (recommend to install it through microsoft visual studio)
    ```bash
    C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.38.33130/include\crtdefs.h(10): fatal error C1083: Cannot open include file: 'corecrt.h': No such file or directory
command 'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\bin\\nvcc.exe' failed with exit code 2
    ```
5. **Inpainting Model**
    For inpainting, we will standardise to `E2FGVI` as it is stated to be more accurate by the research paper
    In main directory, Install `E2FGVI` and `AOT-GAN-for-Inpainting`:
    ```bash
    git clone https://github.com/MCG-NKU/E2FGVI.git
    ```
    - Install the model https://drive.google.com/file/d/10wGdKSUOie0XmCr8SQ2A2FeDe-mfn5w3/view
    put the model in /release_model

    - Download the weights G0000000.pt:
    https://drive.google.com/drive/folders/1bSOH-2nB3feFRyDEmiX81CEiWkghss3i
    and place it in AOT-GAN-for-Inpainting/experiments/

    - Install the other inpainting model (video), it is optional:
    git clone https://github.com/hyunobae/AOT-GAN-for-Inpainting.git
6. **masking.py fix (if you get AssertionError)**
    change this in line 11
    ```python
    from mmdetection.mmdet.apis import inference_detector,init_detector
    with mmdet.apis import inference_detector,init_detector
    ```

7. **Test commands (In order)**
    `DAVIS-test` - contains folders with folders containing sample images from the 480p DAVIS 2016 dataset each:
        -bmx-bumps
        -bmx-trees
    Tree view:
    ```bash
    DAVIS-test/
    │
    ├── JPEGImages/
    │   ├── 480p/
    │   │   ├── bmx-bumps/
    │   │   │   ├── image_0001.jpg
    │   │   │   ├── image_0002.jpg
    │   │   │   └── ...
    │   │   ├── bmx-trees/
    │   │   │   ├── image_0001.jpg
    │   │   │   ├── image_0002.jpg
    │   │   │   └── ...
    │
    ├── Annotations/
    │   ├── 480p/
    │   │   ├── bmx-bumps/
    │   │   │   ├── mask_0001.png
    │   │   │   ├── mask_0002.png
    │   │   │   └── ...
    │   │   ├── bmx-trees/
    │   │   │   ├── mask_0001.png
    │   │   │   ├── mask_0002.png
    │   │   │   └── ...
    ```
    Your folder must include a `.../Annotations/` subdirectory like shown above containing the predetermined masks if you want to use mode 1
        
    ##### 1. Crop (crop.py)
    ```bash
    python crop.py DAVIS-test/JPEGImages/480p/bmx-bumps --width 640 --height 480 --mode 0
    ```
    *(no "/", sample is your folder containing raw images)
    `--mode 0` crops the images in `DAVIS-test/JPEGImages/480p/bmx-bump/` and saves in `cropped/bmx-bumps/`
    `--mode 1` (Requires Step 1. mode 0 to be executed first) crops the masks in `DAVIS-test/Annotations/.../bmx-bumps/` and stores it in `dataset/bmx-bumps/masks/` directory, also moves cropped images from `cropped/bmx-bumps/` to `dataset/bmx-bumps/images/`

    ##### 2. Mask (masking.py)
    ```bash
    python masking.py cropped/bmx-bumps --mode 0
    ``` 
    *(no "/", sample is your folder containing processed images), saves to /dataset dir,
    `--mode 0` is masking using model mask2former,
    `--mode 1` (Requires Step 1. to be in `--mode 1` as well) requires cropped masks in `DAVIS-test/Annotations/.../bmx-bumps/` generated by Step 1. `--mode 1`

    ##### 3. Inpainting (inpaiting.py)
    ```bash
    python inpainting.py dataset/bmx-bumps --model e2fgvi_hq
    ``` 
    `--model` can be: (`--model aotgan`, `--model e2fgvi`, `--model e2fgvi_hq`), saves to /result_inpaint/bmx-bumps/<--model> dir

    ##### 4. Relocating (relocating.py)
    ```bash
    python relocating.py result_inpaint/bmx-bumps/e2fgvi_hq --mode 0
    ```
    `--mode` can be integers `--mode 0`, `--mode 1`, `--mode 2` for: (0:'original', 1:'offset', 2:'dynamic'), saves to /result/bmx-bumps/<--model>/<--mode> dir

    ##### 5. Encoding (encoding.py)
    ```bash
    python encoding.py result/bmx-bumps/e2fgvi_hq/original
    ```
    *original can be:('original', 'offset', 'dynamic'), saves to /video/bmx-bumps dir

8. **Master command (bulk.sh)**
    This master command is to elegantly wrap around all of the previous commands in one .sh file,
    ```bash
    ./bulk.sh <folder> <model> <mode> [--no-mask-model] [--inpaint-only]
    ```
    * `<folder>` - contains folders that would containin sample images each `DAVIS-test/JPEGImages/480p/**/**(.jpg)`
    eg: 480p/breakdance-flare/00000.jpg, test/surf/00001.jpg
    * `<model>` - either 'aotgan', 'e2fgvi', 'e2fgvi_hq'
    * `<mode>` - either 0 for 'original', 1 for 'offset', 2 for 'dynamic'
    * `--no-mask-model` is a flag to set whenever you want to use a segmentation model (in this case its mask2former)
    * `--inpaint-only` to use inpainting network only
    Example:
    - Run without `mask2former` model:
    ```bash 
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p e2fgvi_hq 0 --no-mask-model
    ```
    - Run with `mask2former` model:
    ```bash
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p e2fgvi_hq 0
    ```
    - Run with inpaint only:
    ```bash
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p e2fgvi_hq 0 --inpaint-only
    ```
    (OPTIONAL STEP) Convert MP4 to mov
    ```bash
    python mp4tomov.py <parent folder>
    ```

9. **App to Generate masks from SAM2**
    This app generates masks from SAM2, requires manual input
    ```bash
    cp -f "movetosam2-override/SAM2segmenter.py" "sam2/SAM2segmenter.py"
    python sam2/SAM2segmenter.py <video_parent_dir>
    ```
    * where `<video_parent_dir>` contains folders of images each

    Example:
    ```bash
    cp -f "movetosam2-override/SAM2segmenter.py" "sam2/SAM2segmenter.py"
    python sam2/SAM2segmenter.py C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p
    ```

    (Using bash) Run SAM2 + Crop, then inpaint only**
    To test the flow using SAM2 and inpainting, follow the steps below:
    1. Crop the images then run sam2 on it
    ```bash
    ./cropAndSAM.sh <video_parent_dir>
    ```
    2. Run bulk.sh with only inpainting
    ```bash
    ./bulk.sh <video_parent_dir> e2fgvi_hq 0 --inpaint-only
    ```

    Example:
    ```bash
    ./cropAndSAM.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p e2fgvi_hq 0 --inpaint-only
    ```

10. **Harmonizer**
    - 1. Move to harmonizer
    ```bash
    python prepforharmonizer.py x --mode 0
    ```
    - 2. run the harmonizer
    ```bash
    cd Harmonizer
    python -m demo.image_harmonization.run --example-path ..<Path to folder containing mask and composite sub directory>
    cd ..                           
    ```
    - 3. run encoding
    ```bash
    python encodingHarmonized.py <harmonized folder in path to folder containing mask and composite sub directory>
    ```

    Example:
    ```bash
    python prepforharmonizer.py result --mode 0
    ```
    ```bash
    cd Harmonizer
    python -m demo.image_harmonization.run --example-path ../harmonize/bmx-trees/
    cd ..                           
    ```
    ```bash
    python encodingHarmonized.py harmonize/bmx-trees/harmonized
    ```
11. **workflows**

    - 1. Using mask2former
    ```bash
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p e2fgvi_hq 0
    ```
    - 2. Predefined Segments
    ```bash
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p e2fgvi_hq 0 --no-mask-model
    ```
    - 3. SAM2 + Harmonizer
    ```bash
    ./cropAndSAM.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS-test\JPEGImages\480p e2fgvi_hq 0 --inpaint-only
    ./add_harmonization.sh
    ```
    (On actual dataset)
    ```bash
    ./cropAndSAM.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS\JPEGImages\480p   
    ./bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\DAVIS\JPEGImages\480p e2fgvi_hq 0 --inpaint-only
    ./add_harmonization.sh
    ```