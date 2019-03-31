# encoding: UTF-8

import sys

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy.gateway.bitmex import BitmexGateway
from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.dataRecorder import drEngine

def main():
    """"""
    qapp = create_qapp()
    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(BitmexGateway)
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_engine(drEngine)
    main_window = MainWindow(main_engine, event_engine)
    main_window.showNormal()

    qapp.exec()

if __name__ == "__main__":
    main()
