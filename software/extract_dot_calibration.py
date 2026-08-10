import vuba
import cv2
import glob
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

folder = '/run/user/1000/gvfs/sftp:host=192.168.1.247,user=pi/home/pi/test2'
files_before = glob.glob(f'{folder}/Pos1/*.mkv')
files_after = glob.glob(f'{folder}/Pos1/*.mkv')

# mm_per_px = 70 / 80.5 # Calculate with ImageJ
# mm_per_px = 70 / 59.75 
px_per_mm = 312.415
# search_bbox = (550, 300, 200, 300)

X = []
Y = []
XY = []
for file_before, file_after in zip(files_before[:-1], files_before[1:]):
    try:
        video_before = vuba.Video(file_before)
        img_before = video_before.read(0, grayscale=True)
        img_before = cv2.bitwise_not(img_before)

        video_after = vuba.Video(file_after)
        img_after = video_after.read(0, grayscale=True)
        img_after = cv2.bitwise_not(img_after)
    except:
        continue

    positions = []
    for img in [img_before, img_after]:
        ret, thresh = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)
        contours, hierarchy = vuba.find_contours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
        )

        largest = vuba.largest(contours)
        bboxs = vuba.fit_circles([largest])
        mask = vuba.circle_mask(img, bboxs)

        (x,y),r = bboxs[0]

        positions.append((x, y))
    
        img = vuba.bgr(img)

        vuba.draw_circles(img, bboxs, (0, 255, 0), 2)
        cv2.imshow('test', img)
        cv2.waitKey()

    x_pair, y_pair = list(zip(*positions))
    print('X_pair', x_pair, 'Y_pair', y_pair)

    X.append(np.abs(x_pair[0] - x_pair[1])/px_per_mm)
    Y.append(np.abs(y_pair[0] - y_pair[1])/px_per_mm)
    XY.append(np.sqrt(np.abs(x_pair[0] - x_pair[1])**2 + np.abs(y_pair[0] - y_pair[1])**2)/px_per_mm)

    # cv2.imwrite(re.sub('.mkv', '.png', file), img)

X, Y, XY = map(np.asarray, (X, Y, XY))
X *= 1000
Y *= 1000
XY *= 1000

print(np.mean(X), np.mean(Y), np.mean(XY))

plt.plot(X)
plt.plot(Y)
plt.show()


# px_per_mm = 67.1429 # At resolution captured for this acquisition.
# vals = pd.read_csv('/run/media/z/SSD1/xyz_test3_UoCD/Pos3/images/Results.csv')

# x_sd = np.std(vals.X)
# y_sd = np.std(vals.Y)

# print(x_sd / px_per_mm, y_sd / px_per_mm)

# plt.plot(vals.X[:40], vals.Y[:40], 'ko')
# plt.show()