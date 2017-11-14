import tushare as ts
import requests
import json

from easyquant import DefaultLogHandler
from easyquant import StrategyTemplate
from utils.utils import get_all_highest_druing_previous_days
from eventlet.greenpool import GreenPool
from easyquant.exceptions import NoHistoryData
from datetime import datetime as dt
from oslo_config import cfg

turtle_sys1_opts = [
    cfg.StrOpt('sys1_post_url',
               help='Post result to this url'),
]

CONF = cfg.CONF
CONF.register_opts(turtle_sys1_opts)

class Strategy(StrategyTemplate):
    name = 'turtle system1'

    def __init__(self, user, log_handler, main_engine):
        super(Strategy, self).__init__(user, log_handler, main_engine)
        self.days = 28
        self.post_url = CONF.sys1_post_url

    def init(self):
        self.max_in_previous = {}
        self.breaked_stocks = {}

    def run_before_strategy(self):
        get_all_highest_druing_previous_days(self.days, self.max_in_previous)
        print("init completed")

    def strategy(self, event):
        new_breaked_stocks = False
        for stock, data in event.data.items():
            sinfo = self.max_in_previous.get(stock, None)
            if stock[0:2] not in ['00', '30', '60']:
                continue
            if sinfo is None:
                continue
            if stock not in self.breaked_stocks and \
                    float(data['now']) > float(sinfo['max']):
                break_info = {'name': data['name'],
                              'code': stock,
                              'previous_highest_price': "%0.2f" % sinfo['max'],
                              'break_time':
                              dt.now().strftime(
                                  dt.now().strftime('%Y-%m-%d %H:%M')),
                              'break_price': data['now'],
                              'cv': "%0.2f" % sinfo['cv']}
                self.breaked_stocks[stock] = break_info
                new_breaked_stocks = True

        if new_breaked_stocks:
            requests.post(self.post_url,
                          json=sorted(
                              [x for x in self.breaked_stocks.values()],
                              key=lambda x : x['cv']))
        print("\n")

    def clock(self, event):
        if event.data.clock_event == 'open':
            # 开市了
            self.log.info('open')
        elif event.data.clock_event == 'close':
            # 收市了
            self.log.info('close')
        elif event.data.clock_event == 5:
            # 5 分钟的 clock
            self.log.info("5分钟")
        elif event.data.clock_event == 'newday':
            self.reload()
