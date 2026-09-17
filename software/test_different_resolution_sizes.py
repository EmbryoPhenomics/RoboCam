import vuba
import cv2
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import heartcv as hcv

# MJPG = 0.013 or 1.3 %
# FFV1 = 0.23 or 23 %

px_mb_maps = {
	480: 2.19e-7,
	768: 2.31e-7,
	720: 2.02e-7
	}


video = vuba.Video('/run/media/z/main/laptop_backup/data/A4/*.tif')

frames = video.read(0, len(video), grayscale=False)

writer1 = vuba.Writer('./A4_ffv1_1024x1024.avi', resolution=(1280,720), fps=30, codec='FFV1')
writer2 = vuba.Writer('./A4_mjpg_1024x1024.avi', resolution=(1280,720), fps=30, codec='MJPG')

for frame in tqdm(frames):
	writer1.write(frame)
	writer2.write(frame)

writer1.close()
writer2.close()
video.close()

