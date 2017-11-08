import time
import datetime as dt
from dateutil import tz
from easyquant import DefaultLogHandler
from easyquant import StrategyTemplate
import tushare as ts


class Strategy(StrategyTemplate):
    name = 'system1'
    max_20 = {}

    def strategy(self, event):
        if not self.max_20:
            for stock, data in event.data.items():
                start = (dt.datetime.now() - dt.timedelta(days=20)). \
                    strftime('%Y-%m-%d')
                end = (dt.datetime.now()- dt.timedelta(days=1)). \
                    strftime('%Y-%m-%d')
                hs = ts.get_hist_data(stock, start=start, end=end)
                try:
                    self.max_20[stock] = max(hs['close'])
                    print(stock + " completed max %0.2f" % self.max_20[stock])
                except ValueError:
                    pass
        for stock, data in event.data.items():
            if float(data['now']) > float(self.max_20.get(stock, 100000)):
                print("%s %s now: %s max in previous 20 days: %s" %
                      (stock, data['name'], data['now'],
                       self.max_20.get(stock, 100000)))
        print "=" * 20                

    def clock(self, event):
        """在交易时间会定时推送 clock 事件
        :param event: event.data.clock_event 为 [0.5, 1, 3, 5, 15, 30, 60] 单位为分钟,  ['open', 'close'] 为开市、收市
            event.data.trading_state  bool 是否处于交易时间
        """
        if event.data.clock_event == 'open':
            # 开市了
            self.log.info('open')
        elif event.data.clock_event == 'close':
            # 收市了
            self.log.info('close')
        elif event.data.clock_event == 5:
            # 5 分钟的 clock
            self.log.info("5分钟")
