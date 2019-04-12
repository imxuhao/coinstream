# encoding: UTF-8

from __future__ import print_function

import json
import time
import datetime

import requests
from vnpy.trader.object import BarData
from vnpy.trader.database import DbBarData, DbTickData

config = open('config.json')
setting = json.load(config)
SYMBOLS = setting['SYMBOLS']
APIKEY = setting['APIKEY']
headers = {'Bitmex-API-Key': APIKEY}
# ----------------------------------------------------------------------

def generateVtBar(d):
    """生成K线"""
    bar = BarData(exchange="BITMEX",
                  datetime=datetime.datetime.strptime(d['timestamp'], '%Y-%m-%dT%H:%M:%S.%f0Z'),
                  symbol="XBTUSD",
                  gateway_name="bitmexgateway")
    # bar.symbol = d['symbol']
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

    startDt = datetime.datetime.strptime(start, '%Y%m%d')
    endDt = datetime.datetime.strptime(end, '%Y%m%d')

    url = 'https://www.bitmex.com/api/v1/trade/bucketed'
    params = {
        'binSize': period,
        'partial': 'false',
        'symbol': 'XBTUSD',
        'count': 500,
        'reverse': 'false',
        'startTime': startDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
        'endTime': endDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
    }

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        print(u'%s数据下载失败' % symbol)
        return

    l = resp.json()

    for d in l:
        # {'timestamp': '2018-07-26T02:00:00.000Z', 'symbol': 'XBTUSD', 'open': 8240.5, 'high': 8255.5, 'low': 8206, 'close': 8224.5, 'trades': 17097, 'volume': 73042086, 'vwap': 8229.0981, 'lastSize': 6000, 'turnover': 887640041277, 'homeNotional': 8876.40041276999, 'foreignNotional': 73042086}
        # print(d)
        data = DbBarData(symbol="XBTUSD", exchange="BITMEX",
                         datetime=datetime.datetime.strptime(d['timestamp'], '%Y-%m-%dT%H:%M:%S.%f0Z'),
                         interval="", volume=d['volume'], open_price=d['open'], high_price=d['high'],
                         low_price=d['low'],
                         close_price=d['close'], vt_symbol="BITMEX", gateway_name="bitmexgateway")
        data.save()

    end_time = time.time()
    cost = (end_time - startTime) * 1000

    print(u'合约%s数据下载完成，耗时%s毫秒' % (symbol, cost))


# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def downHourBarBySymbol(symbol, period, start, end):
    """下载hour线数据"""
    startTime = time.time()

    startDt = datetime.datetime.strptime(start, '%Y%m%d')
    endDt = datetime.datetime.strptime(end, '%Y%m%d')

    url = 'https://www.bitmex.com/api/v1/trade/bucketed'
    params = {
        'binSize': period,
        'partial': 'false',
        'symbol': 'XBTUSD',
        'count': 500,
        'reverse': 'false',
        'startTime': startDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
        'endTime': endDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
    }

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        print(u'%s数据下载失败' % symbol)
        return

    l = resp.json()

    for d in l:
        # {'timestamp': '2018-07-26T02:00:00.000Z', 'symbol': 'XBTUSD', 'open': 8240.5, 'high': 8255.5, 'low': 8206, 'close': 8224.5, 'trades': 17097, 'volume': 73042086, 'vwap': 8229.0981, 'lastSize': 6000, 'turnover': 887640041277, 'homeNotional': 8876.40041276999, 'foreignNotional': 73042086}
        # print(d)
        data = DbBarData(symbol="XBTUSD", exchange="BITMEX",
                         datetime=datetime.datetime.strptime(d['timestamp'], '%Y-%m-%dT%H:%M:%S.%f0Z'),
                         interval="1h", volume=d['volume'], open_price=d['open'], high_price=d['high'],
                         low_price=d['low'],
                         close_price=d['close'], vt_symbol="BITMEX", gateway_name="bitmexgateway")
        data.save()

    endTime = time.time()
    cost = (endTime - startTime) * 1000

    print(u'合约%s数据下载完成，耗时%s毫秒' % (symbol, cost))


def downHourBarBySymbol2(symbol, period, startDt, endDt):
    """下载hour线数据"""
    startTime = time.time()

    #    url = 'https://54.230.195.250/api/v1/trade/bucketed'
    url = 'https://www.bitmex.com/api/v1/trade/bucketed'

    params = {
        'binSize': period,
        'partial': 'false',
        'symbol': symbol,
        'count': 500,
        'reverse': 'false',
        'startTime': startDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
        'endTime': endDt.strftime('%Y-%m-%dT%H:%M:%S.%f0Z'),
    }

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        print(u'%s数据下载失败' % symbol)
        return

    l = resp.json()

    for d in l:
        # {'timestamp': '2018-07-26T02:00:00.000Z', 'symbol': 'XBTUSD', 'open': 8240.5, 'high': 8255.5, 'low': 8206, 'close': 8224.5, 'trades': 17097, 'volume': 73042086, 'vwap': 8229.0981, 'lastSize': 6000, 'turnover': 887640041277, 'homeNotional': 8876.40041276999, 'foreignNotional': 73042086}
        # print(d)
        data = DbBarData(symbol=symbol, exchange="BITMEX",
                         datetime=datetime.datetime.strptime(d['timestamp'], '%Y-%m-%dT%H:%M:%S.%f0Z'),
                         interval=period, volume=d['volume'], open_price=d['open'], high_price=d['high'],
                         low_price=d['low'],
                         close_price=d['close'], vt_symbol='%s.%s' % (symbol, 'BITMEX'), gateway_name="bitmexgateway")
        data.save()
        #data.replace()

    endTime = time.time()
    cost = (endTime - startTime) * 1000

    print(u'合约%s数据下载完成，耗时%s毫秒 %s  ----  %s  ' % (symbol, cost, startDt, endDt))

# ----------------------------------------------------------------------


def downloadAllMinuteBar(start, end):
    print('-' * 50)
    print(u'开始下载合约分钟线数据')
    print('-' * 50)

    for symbol in SYMBOLS:
        downMinuteBarBySymbol(symbol, '1MIN', start, end)
        time.sleep(1)

    print('-' * 50)
    print(u'合约分钟线数据下载完成')
    print('-' * 50)



"""
if __name__ == '__main__':
    downMinuteBarBySymbol('XBTUSD', '1m', '20180329', '20180330')

"""

if __name__ == '__main__':
    # downHourBarBySymbol('XBTUSD', '1h', '20170501', '20170531')

    deltaOneday = datetime.timedelta(days=1)
    deltaOnemin = datetime.timedelta(minutes=1)

    startDt = datetime.datetime.strptime('20181110', '%Y%m%d')
    lastDt = datetime.datetime.strptime('20190401', '%Y%m%d')
    while startDt < lastDt:
        endDt = startDt + deltaOneday + deltaOnemin
        downHourBarBySymbol2('XBTUSD', '5m', startDt + deltaOnemin, endDt)
        startDt += deltaOneday
'''T
    startDt = datetime.datetime.strptime('20170701', '%Y%m%d')
    lastDt = datetime.datetime.strptime('20170601', '%Y%m%d')
    (downHourBarBySymbol2'XBTUSD', '1h', startDt + deltaOnemin, startDt  + deltaOneday -deltaOnemin)
'''
# downHourBarBySymbol2('XBTUSD', '1h', startDt,endDt)
# delta = datetime.timedelta(days=3)
