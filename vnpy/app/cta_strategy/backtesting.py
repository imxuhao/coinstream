from collections import defaultdict
from datetime import date, datetime
from typing import Callable
from itertools import product
import multiprocessing

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from mpl_finance import candlestick_ohlc

import seaborn as sns
from pandas import DataFrame

from vnpy.trader.constant import Direction, Exchange, Interval, Status
from vnpy.trader.database import DbBarData, DbTickData
from vnpy.trader.object import OrderData, TradeData
from vnpy.trader.utility import round_to_pricetick

from vnpy.app.cta_strategy.base import (
    BacktestingMode,
    CtaOrderType,
    EngineType,
    ORDER_CTA2VT,
    STOPORDER_PREFIX,
    StopOrder,
    StopOrderStatus,
)
from .template import CtaTemplate

sns.set_style("whitegrid")


class OptimizationSetting:
    """
    Setting for runnning optimization.
    """

    def __init__(self):
        """"""
        self.params = {}
        self.target = ""

    def add_parameter(
            self, name: str, start: float, end: float = None, step: float = None
    ):
        """"""
        if not end and not step:
            self.params[name] = [start]
            return

        if start >= end:
            print("参数优化起始点必须小于终止点")
            return

        if step <= 0:
            print("参数优化步进必须大于0")
            return

        value = start
        value_list = []

        while value <= end:
            value_list.append(value)
            value += step

        self.params[name] = value_list

    def set_target(self, target: str):
        """"""
        self.target = target

    def generate_setting(self):
        """"""
        keys = self.params.keys()
        values = self.params.values()
        products = list(product(*values))

        settings = []
        for p in products:
            setting = dict(zip(keys, p))
            settings.append(setting)

        return settings


class BacktestingEngine:
    """"""
    engine_type = EngineType.BACKTESTING
    gateway_name = "BACKTESTING"

    def __init__(self):
        """"""
        self.vt_symbol = ""
        self.symbol = ""
        self.exchange = None
        self.start = None
        self.end = None
        self.rate = 0  # 回测时假设的佣金比例（适用于百分比佣金）
        self.slippage = 0  # 回测时假设的滑点
        self.size = 1  # 合约大小，默认为1
        self.pricetick = 0  # 价格最小变动
        self.capital = 1_000_000  # 回测时的起始本金（默认100万）
        self.mode = BacktestingMode.BAR  # 回测模式，默认为K线

        self.strategy_class = None
        self.strategy = None
        self.tick = None
        self.bar = None
        self.datetime = None

        self.interval = None
        self.days = 0
        self.callback = None
        self.history_data = []
        # 本地停止单
        self.stop_order_count = 0  # 编号计数：stopOrderID = STOPORDERPREFIX + str(stopOrderCount)
        # 本地停止单字典, key为stopOrderID，value为stopOrder对象
        self.stop_orders = {}  # 停止单撤销后不会从本字典中删除
        self.active_stop_orders = {}

        self.limit_order_count = 0  # 限价单编号
        self.limit_orders = {}  # 限价单字典
        self.active_limit_orders = {}  # 活动限价单字典，用于进行撮合用

        self.trade_count = 0  # 成交编号
        self.trades = {}  # 成交字典

        self.logs = []  # 日志记录

        self.daily_results = {}  # 日线回测结果计算用
        self.daily_df = None

    def clear_data(self):
        """
        Clear all data of last backtesting.
        """
        self.strategy = None
        self.tick = None
        self.bar = None
        self.datetime = None

        self.stop_order_count = 0
        self.stop_orders.clear()
        self.active_stop_orders.clear()

        self.limit_order_count = 0
        self.limit_orders.clear()
        self.active_limit_orders.clear()

        self.trade_count = 0
        self.trades.clear()

        self.logs.clear()
        self.daily_results.clear()

    def set_parameters(
            self,
            vt_symbol: str,
            interval: Interval,
            start: datetime,
            rate: float,
            slippage: float,
            size: float,
            pricetick: float,
            capital: int = 0,
            end: datetime = None,
            mode: BacktestingMode = BacktestingMode.BAR,
    ):
        """"""
        self.mode = mode
        self.vt_symbol = vt_symbol
        self.interval = interval
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.pricetick = pricetick
        self.start = start

        self.symbol, exchange_str = self.vt_symbol.split(".")
        self.exchange = Exchange(exchange_str)

        if capital:
            self.capital = capital

        if end:
            self.end = end

        if mode:
            self.mode = mode

    def add_strategy(self, strategy_class: type, setting: dict):
        """"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(
            self, strategy_class.__name__, self.vt_symbol, setting
        )
        self.strategy.trading = True

    def load_data(self):
        """"""
        self.output("开始加载历史数据")

        if self.mode == BacktestingMode.BAR:
            s = (
                DbBarData.select()
                    .where(
                    (DbBarData.vt_symbol == self.vt_symbol) &
                    (DbBarData.interval == self.interval)
                    & (DbBarData.datetime >= self.start)
                    & (DbBarData.datetime <= self.end)
                ) .order_by(DbBarData.datetime)
            )
            self.history_data = [db_bar.to_bar() for db_bar in s]
        else:
            s = (
                DbTickData.select()
                    .where(
                    (DbTickData.vt_symbol == self.vt_symbol)
                    & (DbTickData.datetime >= self.start)
                    & (DbTickData.datetime <= self.end)
                )
                    .order_by(DbTickData.datetime)
            )
            self.history_data = [db_tick.to_tick() for db_tick in s]

        self.output(f"历史数据加载完成，数据量：{len(self.history_data)}")

    def show_figure(self):
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        data =[s.__dict__ for s in self.history_data]

        df = pd.DataFrame(data,columns=['datetime','open_price','high_price','low_price','close_price'])
        fig, ax = plt.subplots()

        ax.autoscale_view()
        ax.grid(True)
        fig.autofmt_xdate()

        candlestick_ohlc(ax,
                         zip(mdates.date2num(df['datetime']),df['open_price'],df['high_price'],df['low_price'],df['close_price'])
                         ,width=0.02,colordown='r',colorup='g')

        tradenum = []
        tradeinfo = []
        tradenum2 = []
        tradeinfo2 = []

        for trade in self.trades.values():

            if  trade.direction == Direction.LONG:
                tradeinfo.append(trade.price)
                tradenum.append(mdates.date2num(trade.datetime))
            if trade.direction == Direction.SHORT:
                tradeinfo2.append(trade.price)
                tradenum2.append(mdates.date2num(trade.datetime))

        ax.scatter(tradenum,tradeinfo,color='b')
        ax.scatter(tradenum2,tradeinfo2,color='g')

        ax.xaxis_date()

        plt.show()

    def run_backtesting(self):
        """"""
        if self.mode == BacktestingMode.BAR:
            func = self.new_bar
        else:
            func = self.new_tick

        self.strategy.on_init()

        # Use the first [days] of history data for initializing strategy
        day_count = 0
        for ix, data in enumerate(self.history_data):
            if self.datetime and data.datetime.day != self.datetime.day:
                day_count += 1
                if day_count >= self.days:
                    break

            self.datetime = data.datetime
            self.callback(data)

        self.strategy.inited = True
        self.output("策略初始化完成")

        self.strategy.on_start()
        self.strategy.trading = True
        self.output("开始回放历史数据")

        # Use the rest of history data for running backtesting
        for data in self.history_data[ix:]:
            func(data)

        self.output("历史数据回放结束")

    def calculate_result(self):
        """"""
        self.output("开始计算逐日盯市盈亏")

        if not self.trades:
            self.output("成交记录为空，无法计算")
            return

        # Add trade data into daily reuslt.
        for trade in self.trades.values():
            d = trade.datetime.date()
            daily_result = self.daily_results[d]
            daily_result.add_trade(trade)

        # Calculate daily result by iteration.
        pre_close = 0
        start_pos = 0

        for daily_result in self.daily_results.values():
            daily_result.calculate_pnl(
                pre_close, start_pos, self.size, self.rate, self.slippage
            )

            pre_close = daily_result.close_price
            start_pos = daily_result.end_pos

        # Generate dataframe
        results = defaultdict(list)

        for daily_result in self.daily_results.values():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日盯市盈亏计算完成")
        return self.daily_df

    def calculate_statistics(self, df: DataFrame = None):
        """"""
        self.output("开始计算策略统计指标")

        if not df:
            df = self.daily_df

        if df is None:
            # Set all statistics to 0 if no trade.
            start_date = ""
            end_date = ""
            total_days = 0
            profit_days = 0
            loss_days = 0
            end_balance = 0
            max_drawdown = 0
            max_ddpercent = 0
            total_net_pnl = 0
            daily_net_pnl = 0
            total_commission = 0
            daily_commission = 0
            total_slippage = 0
            daily_slippage = 0
            total_turnover = 0
            daily_turnover = 0
            total_trade_count = 0
            daily_trade_count = 0
            total_return = 0
            annual_return = 0
            daily_return = 0
            return_std = 0
            sharpe_ratio = 0
        else:
            # Calculate balance related time series data
            df["balance"] = df["net_pnl"].cumsum() + self.capital
            df["return"] = np.log(df["balance"] / df["balance"].shift(1)).fillna(0)
            df["highlevel"] = (
                df["balance"].rolling(
                    min_periods=1, window=len(df), center=False).max()
            )
            df["drawdown"] = df["balance"] - df["highlevel"]
            df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

            # Calculate statistics value
            start_date = df.index[0]
            end_date = df.index[-1]

            total_days = len(df)
            profit_days = len(df[df["net_pnl"] > 0])
            loss_days = len(df[df["net_pnl"] < 0])

            end_balance = df["balance"].iloc[-1]
            max_drawdown = df["drawdown"].min()
            max_ddpercent = df["ddpercent"].min()

            total_net_pnl = df["net_pnl"].sum()
            daily_net_pnl = total_net_pnl / total_days

            total_commission = df["commission"].sum()
            daily_commission = total_commission / total_days

            total_slippage = df["slippage"].sum()
            daily_slippage = total_slippage / total_days

            total_turnover = df["turnover"].sum()
            daily_turnover = total_turnover / total_days

            total_trade_count = df["trade_count"].sum()
            daily_trade_count = total_trade_count / total_days

            total_return = (end_balance / self.capital - 1) * 100
            annual_return = total_return / total_days * 240
            daily_return = df["return"].mean() * 100
            return_std = df["return"].std() * 100

            if return_std:
                sharpe_ratio = daily_return / return_std * np.sqrt(240)
            else:
                sharpe_ratio = 0

        # Output
        self.output("-" * 30)
        self.output(f"首个交易日：\t{start_date}")
        self.output(f"最后交易日：\t{end_date}")

        self.output(f"总交易日：\t{total_days}")
        self.output(f"盈利交易日：\t{profit_days}")
        self.output(f"亏损交易日：\t{loss_days}")

        self.output(f"起始资金：\t{self.capital:,.2f}")
        self.output(f"结束资金：\t{end_balance:,.2f}")

        self.output(f"总收益率：\t{total_return:,.2f}%")
        self.output(f"年化收益：\t{annual_return:,.2f}%")
        self.output(f"最大回撤: \t{max_drawdown:,.2f}")
        self.output(f"百分比最大回撤: {max_ddpercent:,.2f}%")

        self.output(f"总盈亏：\t{total_net_pnl:,.2f}")
        self.output(f"总手续费：\t{total_commission:,.2f}")
        self.output(f"总滑点：\t{total_slippage:,.2f}")
        self.output(f"总成交金额：\t{total_turnover:,.2f}")
        self.output(f"总成交笔数：\t{total_trade_count}")

        self.output(f"日均盈亏：\t{daily_net_pnl:,.2f}")
        self.output(f"日均手续费：\t{daily_commission:,.2f}")
        self.output(f"日均滑点：\t{daily_slippage:,.2f}")
        self.output(f"日均成交金额：\t{daily_turnover:,.2f}")
        self.output(f"日均成交笔数：\t{daily_trade_count}")

        self.output(f"日均收益率：\t{daily_return:,.2f}%")
        self.output(f"收益标准差：\t{return_std:,.2f}%")
        self.output(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")

        statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
        }

        return statistics

    def show_chart(self, df: DataFrame = None):
        """"""
        if not df:
            df = self.daily_df

        if df is None:
            return

        plt.figure(figsize=(10, 16))

        balance_plot = plt.subplot(4, 1, 1)
        balance_plot.set_title("Balance")
        df["balance"].plot(legend=True)

        drawdown_plot = plt.subplot(4, 1, 2)
        drawdown_plot.set_title("Drawdown")
        drawdown_plot.fill_between(range(len(df)), df["drawdown"].values)

        pnl_plot = plt.subplot(4, 1, 3)
        pnl_plot.set_title("Daily Pnl")
        df["net_pnl"].plot(kind="bar", legend=False, grid=False, xticks=[])

        distribution_plot = plt.subplot(4, 1, 4)
        distribution_plot.set_title("Daily Pnl Distribution")
        df["net_pnl"].hist(bins=50)

        plt.show()

    def run_optimization(self, optimization_setting: OptimizationSetting):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标为设置，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        pool = multiprocessing.Pool(multiprocessing.cpu_count())

        results = []
        for setting in settings:
            result = (pool.apply_async(optimize, (
                target_name,
                self.strategy_class,
                setting,
                self.vt_symbol,
                self.interval,
                self.start,
                self.rate,
                self.slippage,
                self.size,
                self.pricetick,
                self.capital,
                self.end,
                self.mode
            )))
            results.append(result)

        pool.close()
        pool.join()

        # Sort results and output
        result_values = [result.get() for result in results]
        result_values.sort(reverse=True, key=lambda result: result[1])

        for value in result_values:
            msg = f"参数：{value[0]}, 目标：{value[1]}"
            self.output(msg)

        return result_values

    def update_daily_close(self, price: float):
        """"""
        d = self.datetime.date()

        daily_result = self.daily_results.get(d, None)
        if daily_result:
            daily_result.close_price = price
        else:
            self.daily_results[d] = DailyResult(d, price)

    def new_bar(self, bar: DbBarData):
        """"""
        self.bar = bar
        self.datetime = bar.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_bar(bar)

        self.update_daily_close(bar.close_price)

    def new_tick(self, tick: DbTickData):
        """"""
        self.tick = tick
        self.datetime = tick.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_tick(tick)

        self.update_daily_close(tick.last_price)

    def cross_limit_order(self):
        """
        Cross limit order with last bar/tick data.
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.low_price
            short_cross_price = self.bar.high_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
        else:
            long_cross_price = self.tick.ask_price_1
            short_cross_price = self.tick.bid_price_1
            long_best_price = long_cross_price
            short_best_price = short_cross_price

        for order in list(self.active_limit_orders.values()):
            # Push order update with status "not traded" (pending).
            if order.status == Status.SUBMITTING:
                order.status = Status.NOTTRADED
                self.strategy.on_order(order)

            # Check whether limit orders can be filled.
            long_cross = (
                    order.direction == Direction.LONG
                    and order.price >= long_cross_price
                    and long_cross_price > 0
            )

            short_cross = (
                    order.direction == Direction.SHORT
                    and order.price <= short_cross_price
                    and short_cross_price > 0
            )

            if not long_cross and not short_cross:
                continue

            # Push order udpate with status "all traded" (filled).
            order.traded = order.volume
            order.status = Status.ALLTRADED
            self.strategy.on_order(order)

            self.active_limit_orders.pop(order.vt_orderid)

            # Push trade update
            self.trade_count += 1

            if long_cross:
                trade_price = min(order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = max(order.price, short_best_price)
                pos_change = -order.volume

            trade = TradeData(
                symbol=order.symbol,
                exchange=order.exchange,
                orderid=order.orderid,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )
            trade.datetime = self.datetime

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

            self.trades[trade.vt_tradeid] = trade

    def cross_stop_order(self):
        """
        Cross stop order with last bar/tick data.
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.high_price
            short_cross_price = self.bar.low_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
        else:
            long_cross_price = self.tick.last_price
            short_cross_price = self.tick.last_price
            long_best_price = long_cross_price
            short_best_price = short_cross_price

        for stop_order in list(self.active_stop_orders.values()):
            # Check whether stop order can be triggered.
            long_cross = (
                    stop_order.direction == Direction.LONG
                    and stop_order.price <= long_cross_price
            )

            short_cross = (
                    stop_order.direction == Direction.SHORT
                    and stop_order.price >= short_cross_price
            )

            if not long_cross and not short_cross:
                continue

            # Create order data.
            self.limit_order_count += 1

            order = OrderData(
                symbol=self.symbol,
                exchange=self.exchange,
                orderid=str(self.limit_order_count),
                direction=stop_order.direction,
                offset=stop_order.offset,
                price=stop_order.price,
                volume=stop_order.volume,
                status=Status.ALLTRADED,
                gateway_name=self.gateway_name,
            )

            self.limit_orders[order.vt_orderid] = order

            # Create trade data.
            if long_cross:
                trade_price = max(stop_order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = min(stop_order.price, short_best_price)
                pos_change = -order.volume

            self.trade_count += 1

            trade = TradeData(
                symbol=order.symbol,
                exchange=order.exchange,
                orderid=order.orderid,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )
            trade.datetime = self.datetime

            self.trades[trade.vt_tradeid] = trade

            # Update stop order.
            stop_order.vt_orderid = order.vt_orderid
            stop_order.status = StopOrderStatus.TRIGGERED

            self.active_stop_orders.pop(stop_order.stop_orderid)

            # Push update to strategy.
            self.strategy.on_stop_order(stop_order)
            self.strategy.on_order(order)

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

    def load_bar(
            self, vt_symbol: str, days: int, interval: Interval, callback: Callable
    ):
        """"""
        self.days = days
        self.callback = callback

    def load_tick(self, vt_symbol: str, days: int, callback: Callable):
        """"""
        self.days = days
        self.callback = callback

    def send_order(
            self,
            strategy: CtaTemplate,
            order_type: CtaOrderType,
            price: float,
            volume: float,
            stop: bool = False,
    ):
        """"""
        price = round_to_pricetick(price, self.pricetick)
        if stop:
            return self.send_stop_order(order_type, price, volume)
        else:
            return self.send_limit_order(order_type, price, volume)

    def send_stop_order(self, order_type: CtaOrderType, price: float, volume: float):
        """"""
        self.stop_order_count += 1

        stop_order = StopOrder(
            vt_symbol=self.vt_symbol,
            order_type=order_type,
            price=price,
            volume=volume,
            stop_orderid=f"{STOPORDER_PREFIX}.{self.stop_order_count}",
            strategy_name=self.strategy.strategy_name,
        )

        self.active_stop_orders[stop_order.stop_orderid] = stop_order
        self.stop_orders[stop_order.stop_orderid] = stop_order

        return stop_order.stop_orderid

    def send_limit_order(self, order_type: CtaOrderType, price: float, volume: float):
        """"""
        self.limit_order_count += 1
        direction, offset = ORDER_CTA2VT[order_type]

        order = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=str(self.limit_order_count),
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            status=Status.NOTTRADED,
            gateway_name=self.gateway_name,
        )

        self.active_limit_orders[order.vt_orderid] = order
        self.limit_orders[order.vt_orderid] = order

        return order.vt_orderid

    def cancel_order(self, strategy: CtaTemplate, vt_orderid: str):
        """
        Cancel order by vt_orderid.
        """
        if vt_orderid.startswith(STOPORDER_PREFIX):
            self.cancel_stop_order(strategy, vt_orderid)
        else:
            self.cancel_limit_order(strategy, vt_orderid)

    def cancel_stop_order(self, strategy: CtaTemplate, vt_orderid: str):
        """"""
        if vt_orderid not in self.active_stop_orders:
            return
        stop_order = self.active_stop_orders.pop(vt_orderid)

        stop_order.status = StopOrderStatus.CANCELLED
        self.strategy.on_stop_order(stop_order)

    def cancel_limit_order(self, strategy: CtaTemplate, vt_orderid: str):
        """"""
        if vt_orderid not in self.active_limit_orders:
            return
        order = self.active_limit_orders.pop(vt_orderid)

        order.status = Status.CANCELLED
        self.strategy.on_order(order)

    def cancel_all(self, strategy: CtaTemplate):
        """
        Cancel all orders, both limit and stop.
        """
        vt_orderids = list(self.active_limit_orders.keys())
        for vt_orderid in vt_orderids:
            self.cancel_limit_order(strategy, vt_orderid)

        stop_orderids = list(self.active_stop_orders.keys())
        for vt_orderid in stop_orderids:
            self.cancel_stop_order(strategy, vt_orderid)

    def write_log(self, msg: str, strategy: CtaTemplate = None):
        """
        Write log message.
        """
        msg = f"{self.datetime}\t{msg}"
        self.logs.append(msg)

    def send_email(self, msg: str, strategy: CtaTemplate = None):
        """
        Send email to default receiver.
        """
        pass

    def get_engine_type(self):
        """
        Return engine type.
        """
        return self.engine_type

    def put_strategy_event(self, strategy: CtaTemplate):
        """
        Put an event to update strategy status.
        """
        pass

    def output(self, msg):
        """
        Output message of backtesting engine.
        """
        print(f"{datetime.now()}\t{msg}")


class DailyResult:
    """"""

    def __init__(self, date: date, close_price: float):
        """"""
        self.date = date
        self.close_price = close_price
        self.pre_close = 0

        self.trades = []
        self.trade_count = 0

        self.start_pos = 0
        self.end_pos = 0

        self.turnover = 0
        self.commission = 0
        self.slippage = 0

        self.trading_pnl = 0
        self.holding_pnl = 0
        self.total_pnl = 0
        self.net_pnl = 0

    def add_trade(self, trade: TradeData):
        """"""
        self.trades.append(trade)

    def calculate_pnl(
            self,
            pre_close: float,
            start_pos: float,
            size: int,
            rate: float,
            slippage: float,
    ):
        """"""
        self.pre_close = pre_close

        # Holding pnl is the pnl from holding position at day start
        self.start_pos = start_pos
        self.end_pos = start_pos
        self.holding_pnl = self.start_pos * \
                           (self.close_price - self.pre_close) * size

        # Trading pnl is the pnl from new trade during the day
        self.trade_count = len(self.trades)

        for trade in self.trades:
            if trade.direction == Direction.LONG:
                pos_change = trade.volume
            else:
                pos_change = -trade.volume

            turnover = trade.price * trade.volume * size

            self.trading_pnl += pos_change * \
                                (self.close_price - trade.price) * size
            self.end_pos += pos_change
            self.turnover += turnover
            self.commission += turnover * rate
            self.slippage += trade.volume * size * slippage

        # Net pnl takes account of commission and slippage cost
        self.total_pnl = self.trading_pnl + self.holding_pnl
        self.net_pnl = self.total_pnl - self.commission - self.slippage


def optimize(
        target_name: str,
        strategy_class: CtaTemplate,
        setting: dict,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        rate: float,
        slippage: float,
        size: float,
        pricetick: float,
        capital: int,
        end: datetime,
        mode: BacktestingMode,
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
        mode=mode
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    statistics = engine.calculate_statistics()

    target_value = statistics[target_name]
    return (str(setting), target_value, statistics)
