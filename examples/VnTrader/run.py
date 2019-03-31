# encoding: UTF-8

# 重载sys模块，设置默认字符串编码方式为utf8
from importlib import reload

# vn.trader模块
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

import sys
import platform
# 加载底层接口
from vnpy.gateway.bitmex import BitmexGateway
from vnpy.gateway.futu import FutuGateway
from vnpy.gateway.ib import IbGateway
from vnpy.gateway.ctp import CtpGateway
# 加载上层应用
#from vnpy.trader.app import (riskManager, ctaStrategy,
#                             spreadTrading, algoTrading,
#                             tradeCopy)
from vnpy.app.cta_strategy import CtaStrategyApp

reload(sys)
system = platform.system()


def main():
    """"""
    qapp = create_qapp()
    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(CtpGateway)
    main_engine.add_gateway(IbGateway)
    main_engine.add_gateway(FutuGateway)
    main_engine.add_gateway(BitmexGateway)

    main_engine.add_app(CtaStrategyApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showNormal()

    qapp.exec()


if __name__ == "__main__":
    main()
