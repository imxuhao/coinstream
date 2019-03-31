# By Traders, For Traders.

1. 整合了多种交易接口，并针对具体策略算法和功能开发提供了简洁易用的API，用于快速构建交易员所需的量化交易应用。

2. 覆盖国内外所有交易品种的交易接口：

    * CTP(ctpGateway)：国内期货、期权

    * 富途证券(futuGateway)：港股、每股

    * Interactive Brokers(ibGateway)：全球证券、期货、期权、外汇等

    * BitMEX (bitmexGateway)：数字货币期货、期权、永续合约

3. 开箱即用的各类量化策略交易应用：

    * CtaStrategy：CTA策略引擎模块，在保持易用性的同时，允许用户针对CTA类策略运行过程中委托的报撤行为进行细粒度控制（降低交易滑点、实现高频策略）

4. Python交易API接口封装（api），提供上述交易接口的底层对接实现。

5. 简洁易用的事件驱动引擎（event），作为事件驱动型交易程序的核心。





