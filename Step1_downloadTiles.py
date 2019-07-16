# coding=utf-8
import urllib2 as ulb
import numpy as np
import PIL.ImageFile as ImageFile
import cv2
import math
import random
import time
import os

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


# 用户输入更新后的IP文件，如果没有则用代码中的默认IP
ip_path = raw_input("Input the path of IP list file(input \'no\' means use default IPs):\n")
# 判断是否输入IP文件
if ip_path != 'no':
    proxy_list = []
    file = open(ip_path)
    lines = file.readlines()
    for line in lines:
        proxy_list.append(line.strip('\n'))
    print proxy_list.__len__(), 'IPs are loaded.'

# 输入两次请求间的暂停时间
t = input("Input the interval time(second) of requests(e.g. 0.1):\n")

# 输入最大尝试连接次数
maxTryNum = input("Input max  number of try connection(e.g. 5):\n")

# 输入影像层数
z = raw_input("Input image level(0-18):\n")

# 输入左上角点经纬度并计算行列号
lt_raw = raw_input("Input lat & lon at left top(e.g. 30.52N,114.36E):\n")
lt_lat, lt_lon = getNum2(lt_raw)
lt_X, lt_Y = calcXY(lt_lat, lt_lon, z)

# 输入右下角点经纬度并计算行列号
rb_raw = raw_input("Input lat & lon at right bottom(e.g. 30.51N,114.37E):\n")
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

# 输入保存路径
base = raw_input("Input save path:\n")

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
            tile = getTile(url)
            # 保存瓦片
            cv2.imwrite(path, tile)
            # 计数变量增加
            count = count + 1
            # 输出进度信息
            print (round((float(count) / float(tiles)) * 100, 2)).__str__() + " % finished"

# 输出下载完成信息
print rows * cols, 'in total,', (rows * cols - err_urls.__len__()), 'successful,', (err_urls.__len__()), 'unsuccessful.'

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
