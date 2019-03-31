from vnpy.trader.database import DbBarData, DbTickData
DbBarData.insert()
print(DbBarData.select())