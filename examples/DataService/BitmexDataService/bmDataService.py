# encoding: UTF-8

from __future__ import print_function

import json
import time
import datetime

import requests
from pymongo import MongoClient, ASCENDING

from vnpy.trader.object import BarData

# from vnpy.app.cta_strategy.base import MINUTE_DB_NAME
MINUTE_DB_NAME = 'VnTrader_1Min_Db'
# 加载配置
config = open('config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
APIKEY = setting['APIKEY']
SYMBOLS = setting['SYMBOLS']

mc = MongoClient(MONGO_HOST, MONGO_PORT)  # Mongo连接
db = mc[MINUTE_DB_NAME]  # 数据库
headers = {'Bitmex-API-Key': APIKEY}


# ----------------------------------------------------------------------
"""
def generateVtBar(symbol, d):
    
    l = symbol.split('_')
    bar = BarData()
    bar.symbol = l[-2] + l[-1]
    bar.exchange = l[0]
    bar.vtSymbol = '/'.join([bar.symbol, bar.exchange])
    bar.datetime = datetime.datetime.strptime(d['time_open'], '%Y-%m-%dT%H:%M:%S.%f0Z')
    bar.date = bar.datetime.strftime('%Y%m%d')
    bar.time = bar.datetime.strftime('%H:%M:%S')
    bar.open = d['price_open']
    bar.high = d['price_high']
    bar.low = d['price_low']
    bar.close = d['price_close']
    bar.volume = d['volume_traded']

    return bar

"""


def generateVtBar(d):
    """生成K线"""
    bar = BarData(symbol="bar.symbol",
                exchange="bar.exchange",
                datetime=datetime.datetime.strptime(d['timestamp'], '%Y-%m-%dT%H:%M:%S.%f0Z'),
                gateway_name="bar.gateway_name")

   #bar.vtSymbol = '/'.join([bar.symbol, bar.exchange])
    #bar.datetime = datetime.datetime.strptime(d['time_open'], '%Y-%m-%dT%H:%M:%S.%f0Z')
    bar.date = bar.datetime.strftime('%Y%m%d')
    bar.time = bar.datetime.strftime('%H:%M:%S')
    bar.open = d['open']
    bar.high = d['high']
    bar.low = d['low']
    bar.close = d['close']
    bar.volume = d['volume']
    return bar


# ----------------------------------------------------------------------
def downMinuteBarBySymbol(symbol, period, start, end):
    """下载某一合约的分钟线数据"""
    startTime = time.time()

    cl = db[symbol]
    cl.ensure_index([('datetime', ASCENDING)], unique=True)

    startDt = datetime.datetime.strptime(start, '%Y%m%d')
    endDt = datetime.datetime.strptime(end, '%Y%m%d')

    url = 'https://www.bitmex.com/api/v1/trade/bucketed'
    params = {
        'binSize': '1h',
        'partial': 'false',
        'symbol': 'XBTUSD',
        # 'filter': "",
        # 'columns': "",
        'count': 10,
        # 'start': 10000,
        'reverse': 'false',
        'startTime': startDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
        'endTime': endDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
    }

    # binSize	时间周期，可选参数包括1m,5m,1h,1d
    # partial	是否返回未完成的K线
    # symbol	合约类型，如永续合约:XBTUSD
    # filter	返回筛选值，格式{"key":"value"}
    # columns	返回字段值，留空的话返回所有
    # count	返回K线的条数
    # start	起始数据点
    # reverse	是否显示最近的数据，即按时间降序排列
    # startTime	开始时间，格式：2018-06-23T00:00:00.000Z
    # endTime	结束时间，格式：2018-07-23T00:00:00.000Z

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        print(u'%s数据下载失败' % symbol)
        return

    l = resp.json()

    for d in l:
        bar = generateVtBar(d)
        d = bar.__dict__
        flt = {'datetime': bar.datetime}
        cl.replace_one(flt, d, True)
    endTime = time.time()
    cost = (endTime - startTime) * 1000

    print(u'合约%s数据下载完成%s - %s，耗时%s毫秒' % (symbol, l[0]['time_period_start'],
                                         l[-1]['time_period_end'], cost))


# ----------------------------------------------------------------------
def downloadAllMinuteBar(start, end):
    """下载所有配置中的合约的分钟线数据"""
    print('-' * 50)
    print(u'开始下载合约分钟线数据')
    print('-' * 50)

    for symbol in SYMBOLS:
        downMinuteBarBySymbol(symbol, '1MIN', start, end)
        time.sleep(1)

    print('-' * 50)
    print(u'合约分钟线数据下载完成')
    print('-' * 50)


if __name__ == '__main__':
    downMinuteBarBySymbol('BITMEX_SPOT_BTC_USDT', '1MIN', '20180725', '20180726')
