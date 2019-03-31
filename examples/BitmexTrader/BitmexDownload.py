

#https://www.bitmex.com/api/v1/trade/bucketed?binSize=1h&partial=false&symbol=XBTUSD&count=500&reverse=false&startTime=2015-09-25T00:00:00.000Z

#获取K线  请求地址:
#https://www.bitmex.com/api/v1/trade/bucketed
#请求方式：get

#参数：

#binSize	时间周期，可选参数包括1m,5m,1h,1d
#partial	是否返回未完成的K线
#symbol	合约类型，如永续合约:XBTUSD
#filter	返回筛选值，格式{"key":"value"}
#columns	返回字段值，留空的话返回所有
#count	返回K线的条数
#start	起始数据点
#reverse	是否显示最近的数据，即按时间降序排列
#startTime	开始时间，格式：2018-06-23T00:00:00.000Z
#endTime	结束时间，格式：2018-07-23T00:00:00.000Z
#如获取小时级别k线的URL地址为
# ：https://www.bitmex.com/api/v1/trade/bucketed?binSize=1h&partial=false&symbol=XBTUSD&count=500&reverse=false&startTime=2015-09-25T00:00:00.000Z

