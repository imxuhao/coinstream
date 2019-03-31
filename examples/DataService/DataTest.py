# encoding: UTF-8
import json
import time
import datetime
import requests
from pymongo import MongoClient,ASCENDING


config = open('config.json')
setting = json.load(config)
MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']

mc = MongoClient(MONGO_HOST , MONGO_PORT)
db = mc['VnTrader_1Min_Db']                                         # 数据库
dbDaily = mc['VnTrader_Daily_Db']

dblist= mc.list_database_names()

print(dblist)

mylist = [
    {"name": "Taobao", "alexa": "100", "url": "https://www.taobao.com"},
    {"name": "QQ", "alexa": "101", "url": "https://www.qq.com"},
    {"name": "Facebook", "alexa": "10", "url": "https://www.facebook.com"},
    {"name": "知乎", "alexa": "103", "url": "https://www.zhihu.com"},
    {"name": "Github", "alexa": "109", "url": "https://www.github.com"}
]
mycol = db["sites"]
x = mycol.insert_many(mylist)
print(x)
