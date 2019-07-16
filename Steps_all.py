# coding=utf-8
import os

if __name__ == '__main__':
    print "------Step 1:download tiles------"
    os.system("python Step1_downloadTiles.py")
    print "------Step 1 finished------"
    print "------Step 2:join tiles into one image------"
    os.system("python Step2_joinTiles.py")
    print "------Step 2 finished------"
    print "------Step 3:convert image to tiff with geo-information------"
    os.system("python Step3_generateTif.py")
    print "------Step 3 finished------"
