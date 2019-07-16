# coding=utf-8
import urllib2 as ulb
import numpy as np
import PIL.ImageFile as ImageFile
import cv2
import math
import random
import time
import os
import sys
from osgeo import gdal
from gdalconst import *

# 免费代理IP不能保证永久有效，如果不能用可以更新
# https://www.goubanjia.com/
proxy_list = [
    '117.143.109.167:80',
    '117.143.109.130:80',
    '117.143.109.136:80',
    '117.143.109.163:80',
    '61.136.163.245:3128',
    '180.97.250.89:80',
    '180.97.250.90:80',
    '117.143.109.161:80',
    '166.111.77.32:80',
    '61.136.163.245:3128'
]

# 收集到的常用Header
my_headers = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "
]

# 用于存放获取失败瓦片的url、path
err_urls = []
err_paths = []

# 记录经过尝试仍然失败的瓦片
err_final_url = []

t = 0.1
maxTryNum = 5
z = 18


# 获取瓦片函数
def getTile(url, path):
    # 每次执行前先暂停t秒
    time.sleep(t)

    # 随机选择IP、Header
    proxy = random.choice(proxy_list)
    header = random.choice(my_headers)

    print proxy, 'sleep:', t
    print header
    print "\n"

    # 基于选择的IP构建连接
    urlhandle = ulb.ProxyHandler({'http': proxy})
    opener = ulb.build_opener(urlhandle)
    ulb.install_opener(opener)

    # 按照最大尝试次数连接
    for tries in range(maxTryNum):
        try:
            # 用urllib2库链接网络图像
            response = ulb.Request(url)

            # 增加Header伪装成浏览器
            response.add_header('User-Agent', header)
            # 打开网络图像文件句柄
            fp = ulb.urlopen(response)

            # 定义图像IO
            p = ImageFile.Parser()

            # 开始图像读取
            while 1:
                s = fp.read(1024)
                if not s:
                    break
                p.feed(s)

            # 得到图像
            im = p.close()
            # 将图像转换成numpy矩阵
            arr = np.array(im)
            # 将通道顺序变成BGR，以便OpenCV可以正确保存
            arr = arr[:, :, ::-1]
            return arr
        # 抛出异常
        except ulb.HTTPError, e:
            # 持续尝试
            if tries < (maxTryNum - 1):
                # 404错误直接退出
                if e.code == 404:
                    print '***404 Not Found***'
                    arr = np.zeros((256, 256, 3), np.uint8)
                    # 将该url、path记录到list中
                    err_urls.append(url)
                    err_paths.append(path)
                    break
                # 403错误直接退出
                elif e.code == 403:
                    print '!!!403 Forbidden!!!'
                    arr = np.zeros((256, 256, 3), np.uint8)
                    err_urls.append(url)
                    err_paths.append(path)
                    break
                # 打印尝试次数
                print (tries + 1), "time(s) to access", url
                continue
            else:
                # 输出失败信息
                print "Has tried", maxTryNum, "times to access", url, ", all failed!"
                arr = np.zeros((256, 256, 3), np.uint8)
                err_urls.append(url)
                err_paths.append(path)
    # 统一返回arr
    return arr


# 用于对失败的瓦片重新获取
def errTile(url):
    # 每次执行前先暂停t秒
    time.sleep(t)

    # 随机选择IP、Header
    proxy = random.choice(proxy_list)
    header = random.choice(my_headers)

    print proxy, 'sleep:', t, header

    # 基于选择的IP构建连接
    urlhandle = ulb.ProxyHandler({'http': proxy})
    opener = ulb.build_opener(urlhandle)
    ulb.install_opener(opener)

    # 按照最大尝试次数连接
    for tries in range(maxTryNum):
        try:
            # 用urllib2库链接网络图像
            response = ulb.Request(url)

            # 增加Header伪装成浏览器
            response.add_header('User-Agent', header)
            # 打开网络图像文件句柄
            fp = ulb.urlopen(response)

            # 定义图像IO
            p = ImageFile.Parser()

            # 开始图像读取
            while 1:
                s = fp.read(1024)
                if not s:
                    break
                p.feed(s)

            # 得到图像
            im = p.close()
            # 将图像转换成numpy矩阵
            arr = np.array(im)
            # 将通道顺序变成BGR，以便OpenCV可以正确保存
            arr = arr[:, :, ::-1]
            return arr
        # 抛出异常
        except ulb.HTTPError, e:
            # 持续尝试
            if tries < (maxTryNum - 1):
                # 404错误直接退出
                if e.code == 404:
                    print '***404 Not Found***'
                    arr = np.zeros((256, 256, 3), np.uint8)
                    err_final_url.append(url)
                    break
                # 403错误直接退出
                elif e.code == 403:
                    print '!!!403 Forbidden!!!'
                    arr = np.zeros((256, 256, 3), np.uint8)
                    err_final_url.append(url)
                    break
                # 打印尝试次数
                print (tries + 1), "time(s) to access", url
                continue
            else:
                # 输出失败信息
                print "Has tried", maxTryNum, "times to access", url, ", all failed!"
                arr = np.zeros((256, 256, 3), np.uint8)
                err_final_url.append(url)
    # 统一返回arr
    # 将通道顺序变成BGR，以便OpenCV可以正确保存
    arr = arr[:, :, ::-1]
    return arr


# 由x、y、z计算瓦片行列号
def calcXY(lat, lon, z):
    x = math.floor(math.pow(2, int(z) - 1) * ((lon / 180.0) + 1))
    tan = math.tan(lat * math.pi / 180.0)
    sec = 1.0 / math.cos(lat * math.pi / 180.0)
    log = math.log(tan + sec)
    y = math.floor(math.pow(2, int(z) - 1) * (1 - log / math.pi))
    return int(x), int(y)


# 字符串度分秒转度
def cvtStr2Deg(deg, min, sec):
    result = int(deg) + int(min) / 60.0 + float(sec) / 3600.0
    return result


# 获取经纬度
def getNum(str):
    split = str.split(',')
    du = split[0].split('°')[0]
    fen = split[0].split('°')[1].split('\'')[0]
    miao = split[0].split('°')[1].split('\'')[1].split('"')[0]
    split1 = cvtStr2Deg(du, fen, miao)
    du = split[1].split('°')[0]
    fen = split[1].split('°')[1].split('\'')[0]
    miao = split[1].split('°')[1].split('\'')[1].split('"')[0]
    split2 = cvtStr2Deg(du, fen, miao)
    return split1, split2


# 获取经纬度
def getNum2(str):
    split = str.split(',')
    split1 = float(split[0].split('N')[0])
    split2 = float(split[1].split('E')[0])
    return split1, split2


# 计算经纬度
def calcLatLon(x, y, z, m, n):
    lon = (math.pow(2, 1 - z) * (x + m / 256.0) - 1) * 180.0
    lat = (360 * math.atan(math.pow(math.e, (1 - math.pow(2, 1 - z) * (y + n / 256.0)) * math.pi))) / math.pi - 90
    return lat, lon


def loadData(dirtctory):
    files = []
    for parent, dirname, filenames in os.walk(dirtctory):
        for filename in filenames:
            name = parent + filename
            if name.__contains__("output"):
                files.append(name)
    print 'Data are loaded.'
    return files


def readImage(img_path):
    data = []
    # 以只读方式打开遥感影像
    dataset = gdal.Open(img_path, GA_ReadOnly)
    if dataset is None:
        print("Unable to open image file.")
        return data
    else:
        print("Open image file success.")
        geoTransform = dataset.GetGeoTransform()
        im_proj = dataset.GetProjection()  # 获取投影信息
        bands_num = dataset.RasterCount
        print("Image height:" + dataset.RasterYSize.__str__() + " Image width:" + dataset.RasterXSize.__str__())
        print(bands_num.__str__() + " bands in total.")
        for i in range(bands_num):
            # 获取影像的第i+1个波段
            band_i = dataset.GetRasterBand(i + 1)
            # 读取第i+1个波段数据
            band_data = band_i.ReadAsArray(0, 0, band_i.XSize, band_i.YSize)
            data.append(band_data)
            print("band " + (i + 1).__str__() + " read success.")
        return data


def writeImage(bands, path, geotrans=None, proj=None):
    projection = [
        # WGS84坐标系(EPSG:4326)
        """GEOGCS["WGS 84", DATUM["WGS_1984", SPHEROID["WGS 84", 6378137, 298.257223563, AUTHORITY["EPSG", "7030"]], AUTHORITY["EPSG", "6326"]], PRIMEM["Greenwich", 0, AUTHORITY["EPSG", "8901"]], UNIT["degree", 0.01745329251994328, AUTHORITY["EPSG", "9122"]], AUTHORITY["EPSG", "4326"]]""",
        # Pseudo-Mercator、球形墨卡托或Web墨卡托(EPSG:3857)
        """PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs"],AUTHORITY["EPSG","3857"]]"""
    ]

    if bands is None or bands.__len__() == 0:
        return
    else:
        # 认为各波段大小相等，所以以第一波段信息作为保存
        band1 = bands[0]
        # 设置影像保存大小、波段数
        img_width = band1.shape[1]
        img_height = band1.shape[0]
        num_bands = bands.__len__()

        # 设置保存影像的数据类型
        if 'int8' in band1.dtype.name:
            datatype = gdal.GDT_Byte
        elif 'int16' in band1.dtype.name:
            datatype = gdal.GDT_UInt16
        else:
            datatype = gdal.GDT_Float32

        # 创建文件
        driver = gdal.GetDriverByName("GTiff")
        dataset = driver.Create(path, img_width, img_height, num_bands, datatype)
        if dataset is not None:
            if geotrans is not None:
                dataset.SetGeoTransform(geotrans)  # 写入仿射变换参数
            if proj is not None:
                if proj is 'WGS84' or proj is 'wgs84' or proj is 'EPSG:4326' or proj is 'EPSG-4326' or proj is '4326':
                    dataset.SetProjection(projection[0])  # 写入投影
                elif proj is 'EPSG:3857' or proj is 'EPSG-3857' or proj is '3857':
                    dataset.SetProjection(projection[1])  # 写入投影
                else:
                    dataset.SetProjection(proj)  # 写入投影
            for i in range(bands.__len__()):
                dataset.GetRasterBand(i + 1).WriteArray(bands[i])
        print("save image success.")


def genGeoTrans(file_path):
    f = open(file_path)
    f.readline()
    nw_line = f.readline().strip()
    f.readline()
    nw_latlon = f.readline().strip()
    f.readline()
    se_line = f.readline().strip()
    f.readline()
    se_latlon = f.readline().strip()
    row_num = f.readline().strip()
    col_num = f.readline().strip()
    f.readline()
    img_size = f.readline().strip()
    nw_lat = float(nw_latlon.split(",")[0])
    nw_lon = float(nw_latlon.split(",")[1])
    se_lat = float(se_latlon.split(",")[0])
    se_lon = float(se_latlon.split(",")[1])
    img_w = int(img_size.split("*")[0])
    img_h = int(img_size.split("*")[1])
    reso_x = (se_lon - nw_lon) / img_w
    reso_y = (nw_lat - se_lat) / img_h
    return (nw_lon, reso_x, 0, nw_lat, 0, reso_y)


if __name__ == '__main__':
    if len(sys.argv) != 8:
        print "wrong arguments for program,please check."
        exit()

    ip_path = sys.argv[1]  # the path of IP list file('no' means use default IPs)
    t = float(sys.argv[2])  # the interval time(second) of requests(e.g. 0.1)
    maxTryNum = int(sys.argv[3])  # max number of try connection(e.g. 5)
    z = int(sys.argv[4])  # image level(0-18)
    lt_raw = sys.argv[5]  # lat & lon at left top(e.g. 30.52N,114.36E)
    rb_raw = sys.argv[6]  # lat & lon at right bottom(e.g. 30.51N,114.37E)
    base = sys.argv[7] + os.sep  # work directory for saving tiles and image

    print "------Step 1:download tiles------"
    # 判断是否输入IP文件 用户输入更新后的IP文件，如果没有则用代码中的默认IP
    if ip_path != 'no':
        proxy_list = []
        file = open(ip_path)
        lines = file.readlines()
        for line in lines:
            proxy_list.append(line.strip('\n'))
        print proxy_list.__len__(), 'IPs are loaded.'

    # 输入左上角点经纬度并计算行列号
    lt_lat, lt_lon = getNum2(lt_raw)
    lt_X, lt_Y = calcXY(lt_lat, lt_lon, z)

    # 输入右下角点经纬度并计算行列号
    rb_lat, rb_lon = getNum2(rb_raw)
    rb_X, rb_Y = calcXY(rb_lat, rb_lon, z)

    # 计算行列号差值及瓦片数
    cols = rb_X - lt_X
    rows = rb_Y - lt_Y
    tiles = cols * rows
    count = 0

    # 判断结果是否合理
    if tiles <= 0:
        print 'Please check your input.'
        exit()
    print tiles.__str__() + ' tiles will be downloaded.'

    print 'Now start...'

    # 循环遍历，下载瓦片
    for i in range(rows):
        for j in range(cols):
            # 拼接url
            url = 'https://mt2.google.cn/vt/lyrs=s&hl=zh-CN&gl=CN&x=' + (j + lt_X).__str__() + '&y=' + (
                    i + lt_Y).__str__() + '&z=' + z.__str__()
            # 拼接输出路径
            path = base + '\\' + z.__str__() + '_' + (j + lt_X).__str__() + '_' + (i + lt_Y).__str__() + '.jpg'

            # 判断是否已有瓦片文件
            if os.path.exists(path):
                temp_tile = cv2.imread(path, 0)
                # 判断文件内容是否为空
                if temp_tile[100, 100] == 0:
                    # 获取瓦片
                    tile = getTile(url, path)
                    # 保存瓦片
                    cv2.imwrite(path, tile)
                    # 计数变量增加
                    count = count + 1
                    # 输出进度信息
                    print (round((float(count) / float(tiles)) * 100, 2)).__str__() + " % finished"
                else:
                    # 计数变量增加
                    count = count + 1
                    print (round((float(count) / float(tiles)) * 100, 2)).__str__() + " % finished"
                continue
            else:
                # 获取瓦片
                tile = getTile(url, path)
                # 保存瓦片
                cv2.imwrite(path, tile)
                # 计数变量增加
                count = count + 1
                # 输出进度信息
                print (round((float(count) / float(tiles)) * 100, 2)).__str__() + " % finished"

    # 输出下载完成信息
    print rows * cols, 'in total,', (rows * cols - err_urls.__len__()), 'successful,', (
        err_urls.__len__()), 'unsuccessful.'

    # 如果不成功瓦片列表不为0，再次尝试
    if err_urls.__len__() != 0:
        print 'Trying for unsuccessful tiles again...'
        for k in range(err_urls.__len__()):
            # 获取瓦片
            tile = errTile(err_urls[k])
            # 保存瓦片
            cv2.imwrite(err_paths[k], tile)

    # 如果最终不成功瓦片列表不为0，输出最终不成功瓦片url
    if err_final_url.__len__() != 0:
        # 创建文件
        output = open(base + "\err_output.txt", 'w')
        output.write('Delete this file before join tiles together!\n')
        # 依次输出无法获取瓦片的url
        for i in range(err_final_url.__len__()):
            output.write(err_final_url[i] + '\n')
            print err_final_url[i]
        output.close()
    print "------Step 1 finished------"

    print "------Step 2:join tiles into one image------"
    layer = 18

    # 记录x、y、瓦片
    xs = []
    ys = []
    imgs = []
    paths = []

    # 用户输入存放影像的文件夹目录，如E:\L0
    rootdir = base

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
    print "------Step 2 finished------"

    print "------Step 3:convert image to tiff with geo-information------"
    # 用户输入存放影像的文件夹目录，如E:\L0
    rootdir = base
    img, loc = loadData(rootdir)
    trans = genGeoTrans(loc)
    bands = readImage(img)
    writeImage(bands, rootdir + os.sep + "geoImage.tif", geotrans=trans, proj='wgs84')
    readImage(rootdir + os.sep + "geoImage.tif")
    print "------Step 3 finished------"
