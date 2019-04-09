from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class BiShenStrategy(CtaTemplate):
    author = 'xuhao'
    #7、14、28
    short_window = 7
    mid_window = 14
    long_window = 28

    short_ma0 = 0.0
    short_ma1 = 0.0
    short_ma2 = 0.0
    mid_ma0 = 0.0
    mid_ma1 = 0.0
    mid_ma2 = 0.0
    long_ma0 = 0.0
    long_ma1 = 0.0
    long_ma2 = 0.0

    parameters = ['short_window', 'mid_window', 'long_window']
    variables = ['short_ma0', 'short_ma1', 'mid_ma0', 'mid_ma1', 'long_ma0', 'long_ma1']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(BiShenStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited. TODO
        """
        self.write_log("策略初始化")
        self.load_bar(self.long_window)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return
        n = 10
        n_day_max, n_day_min = am.donchian(n)

        long_ma = am.sma(self.long_window, array=True)
        self.long_ma0 = long_ma[-1]
        self.long_ma1 = long_ma[-2]
        self.long_ma2 = long_ma[-3]

        mid_ma = am.sma(self.mid_window, array=True)
        self.mid_ma0 = mid_ma[-1]
        self.mid_ma1 = mid_ma[-2]
        self.mid_ma2 = mid_ma[-3]

        short_ma = am.sma(self.short_window, array=True)
        self.short_ma0 = short_ma[-1]
        self.short_ma1 = short_ma[-2]
        self.short_ma2 = short_ma[-3]

        #定义上扬：ma（-1）》ma（-2），下降换成《
        long_shangyang = self.long_ma0 > self.long_ma1
        mid_shangyang = self.mid_ma0 > self.mid_ma1
        short_shangyang = self.short_ma0 > self.short_ma1

        #定义发散：ma1（-1）-ma2（-1）》ma1（-2）-ma2（-2）   两两发散
        long_mid_fa_san = abs(self.mid_ma0 - self.long_ma0) > abs(self.mid_ma1 - self.long_ma1)
        mid_short_fa_san = abs(self.short_ma0 - self.mid_ma0) > abs(self.short_ma1 - self.mid_ma1)

        #突破
        if long_shangyang and mid_shangyang and short_shangyang and long_mid_fa_san and mid_short_fa_san:
            self.buy(n_day_max, 1)
            print('上，以{}最高点买入  buy at price {}   {}'.format(n, n_day_max, bar.datetime))

        if not long_shangyang and not mid_shangyang and not short_shangyang and long_mid_fa_san and mid_short_fa_san:
            self.sell(n_day_min, 1)
            print('下，以{}最低点卖出  sell at price {}   {}'.format(n, n_day_min, bar.datetime))

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
