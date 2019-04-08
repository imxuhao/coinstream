# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division
from datetime import datetime
from vnpy.app.cta_strategy.backtesting import BacktestingEngine
from vnpy.app.cta_strategy.base import BacktestingMode

if __name__ == '__main__':
    from vnpy.app.cta_strategy.strategies.double_ma_strategy import DoubleMaStrategy
    from vnpy.app.cta_strategy.strategies.boll_channel_strategy import BollChannelStrategy

    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置产品相关参数
    # 设置引擎的回测模式为K线
    # 设置回测用的数据起始日期
    # 股指1跳
    # 万0.3
    # size 股指合约大小
    # pricetick 股指最小价格变动
    engine.set_parameters(mode=BacktestingMode.BAR,
                          start=datetime.strptime('20170329', '%Y%m%d'),
                          end=datetime.strptime('20190329', '%Y%m%d'),
                          slippage=0.2,
                          rate=(0.3 / 10000),
                          size=300,
                          pricetick=0.2,
                          vt_symbol="XBTUSD.BITMEX",
                          interval="1h")

    # 在引擎中创建策略对象
    d = {'fast_window': 10, 'slow_window': 30}
    engine.add_strategy(DoubleMaStrategy, d)

    engine.load_data()
    # 开始跑回测
    engine.run_backtesting()

    # 显示回测结果
    engine.calculate_result()
    engine.calculate_statistics()
