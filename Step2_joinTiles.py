# coding=utf-8
import cv2
import numpy as np
import os.path
import math


# 计算经纬度
def calcLatLon(x, y, z, m, n):
    lon = (math.pow(2, 1 - z) * (x + m / 256.0) - 1) * 180.0
    lat = (360 * math.atan(math.pow(math.e, (1 - math.pow(2, 1 - z) * (y + n / 256.0)) * math.pi))) / math.pi - 90
    return lat, lon


layer = 18

# 记录x、y、瓦片
xs = []
ys = []
imgs = []
paths = []

# 用户输入存放影像的文件夹目录，如E:\L0
rootdir = raw_input("Input the parent path of images:\n") + "\\"

for parent, dirname, filenames in os.walk(rootdir):
    for filename in filenames:
        name = parent + filename
        # 附加到list
        paths.append(name)

        # 提取x、y、layer并保存在list中
        filename = filename.split('.')
        str = filename[0].split('_')
        if xs.__len__() == 0:
            layer = int(str[0])
        x = int(str[1])
        y = int(str[2])
        xs.append(x)
        ys.append(y)

print 'Images are loaded.'

# 去除list中的重复元素并排序
xs = list(set(xs))
xs.sort()
ys = list(set(ys))
ys.sort()

# 用于存放每一列的拼图
v_lines = []

# 先按照竖直方向拼成条带
for i in range(0, paths.__len__(), ys.__len__()):
    for item in paths[i:i + ys.__len__()]:
        img = cv2.imread(item)
        imgs.append(img)
    v_line = tuple(imgs)
    imgs = []
    v_tuple = np.vstack(v_line)
    v_lines.append(v_tuple)
    print 'Join images', round((i * 1.0 / paths.__len__()) * 100, 2), '% finished'

v_tuple = tuple(v_lines)

# 清空v_lines释放内存
v_lines = []

# 清空paths释放
paths = []

# 再按水平方向拼接
final = np.hstack(v_tuple)

# 清空v_tuple释放内存
v_tuple = []

print 'Writing image...'

# 输出拼接后的图像
cv2.imwrite(parent + "output.jpg", final)

# 输出相关信息
nw_loc = calcLatLon(xs[0], ys[0], layer, 0, 0)
se_loc = calcLatLon(xs[-1], ys[-1], layer, 255, 255)
output = open(parent + "output.txt", 'w')
output.write('north-west point (x,y):\n' + xs[0].__str__() + "," + ys[0].__str__() + "\n")
output.write('north-west point (lat,lon):\n' + nw_loc[0].__str__() + "," + nw_loc[1].__str__() + "\n")
output.write('south-east point (x,y):\n' + xs[-1].__str__() + "," + ys[-1].__str__() + "\n")
output.write('south-east point (lat,lon):\n' + se_loc[0].__str__() + "," + se_loc[1].__str__() + "\n")
output.write('rows:' + xs.__len__().__str__() + "\n")
output.write('columns:' + ys.__len__().__str__() + "\n")
output.write('Output image size:\n' + final.shape[1].__str__() + ' * ' + final.shape[0].__str__())
output.close()

# 控制台中打印相关信息
print '\n'
print 'north-west point (x,y):', (xs[0], ys[0]).__str__()
print 'north-west point (lat,lon):', calcLatLon(xs[0], ys[0], layer, 0, 0)
print 'south-east point (x,y):', (xs[-1], ys[-1]).__str__()
print 'south-east point (lat,lon):', calcLatLon(xs[-1], ys[-1], layer, 255, 255)
print 'rows:', xs.__len__()
print 'columns:', ys.__len__()
print 'Output image size:', final.shape[1].__str__(), '*', final.shape[0].__str__()

print "------------------------"
print "Output files info:"
print parent + "output.jpg"
print parent + "output.txt"
print "------------------------"

# 显示图像，如果图片宽高大于1080则太大，就不在窗口显示了
if final.shape[1] <= 1080 and final.shape[0] <= 1080:
    cv2.imshow("final", final)
    cv2.waitKey(0)
else:
    pass
