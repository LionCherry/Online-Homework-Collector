#!/usr/bin/env python3
'''
The default variables setting for the whole website server.
'''

import os
from distutils.version import StrictVersion

PORT = 5000

INDEX_FILE = "dashboard.bundle.js"
# STATIC_FILE_LIST = os.listdir('./static')
# STATIC_FILE_LIST.sort(key=StrictVersion)
# STATIC_VERSION = STATIC_FILE_LIST[-1]

MONITOR_TIME_PERIOD = 30

DB_USER = '../../user.tsv'
DB_HOMEWORK = '../../homework.tsv'
DB_STATU = '../../statu.tsv'

FILE_SAVE_DIR = '../../Homework'

HOMEWORK_STATU = ['未提交', '已提交', '已结束']
HOMEWORK_ALLOW_EXT = ['cpp','c','h','hpp','rar','zip','doc','docx','txt','tsv','png','jpg','bmp']