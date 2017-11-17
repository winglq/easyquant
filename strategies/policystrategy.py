import tushare as ts
import requests
from eventlet.greenpool import GreenPool
from datetime import datetime, timedelta
from easyquotation.helpers import get_stock_codes
from easyquant import StrategyTemplate
from easyquant.policy.manager import Manager
from easyquant.easydealutils.time import previous_trade_date_from_now


class Strategy(StrategyTemplate):

    def __init__(self, user, log_handler, main_engine):
        super(Strategy, self).__init__(user, log_handler, main_engine)
        self.define_policies()
        self.policy_post_url = None

    @staticmethod
    def get_hist_data(code):
        start_date = previous_trade_date_from_now(65)
        end_date = datetime.now() - timedelta(days=1)
        strstart = start_date.strftime('%Y-%m-%d')
        strend = end_date.strftime('%Y-%m-%d')
        hist = ts.get_hist_data(code, start=strstart, end=strend)
        return hist

    def run_before_strategy(self):
        if self.manager.load_indicators():
            return
        stock_codes = get_stock_codes()
        gp = GreenPool()
        for code in stock_codes:
            if code[0: 2] not in ['00', '60', '30']:
                continue
            gp.spawn(self.manager.prepare,
                     code, Strategy.get_hist_data)
        gp.waitall()
        self.manager.save()

    def strategy(self, event):
        result = self.manager.run(event.data)
        print(result['system4'])
        for policy, data in result.items():
            if data['updated'] and self.policy_post_url:
                requests.post(self.policy_post_url,
                              json = data['result'])


    def define_policies(self):
        self.manager = Manager()
        self.manager.indicator_create('edge_cls', name='highest_20',
                                      column='high', days=20)
        self.manager.indicator_create('edge_cls', name='highest_60',
                                      column='high', days=60)
        self.manager.indicator_create('cv_cls', name='cv_20', column='close',
                                      days=20)
        self.manager.indicator_create('cv_cls', name='cv_60', column='close',
                                      days=60)

        self.manager.indicator_create("continuouse_red_days_cls",
                                      name='redday_60',
                                      expected_continuous_days=3,
                                      days=60)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_500',
                                         500)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_2',
                                         2)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_8',
                                         8)
        self.manager.get_val_func_create('get_value_by_key_func', 'key_now',
                                         'now')
        self.manager.rule_create('highest_20_rule', "key_now", '>',
                                 'highest_20')
        self.manager.rule_create('highest_60_rule', "key_now", '>',
                                 'highest_60')
        self.manager.rule_create('cv_20_rule', "fix_500", '>',
                                 'cv_20')
        self.manager.rule_create('cv_60_rule', "fix_500", '>',
                                 'cv_60')
        self.manager.rule_create('cv_60_strict_rule', "fix_2", '>',
                                 'cv_60')
        self.manager.rule_create('redday_60_rule', "fix_2", '<',
                                 'redday_60')
        self.manager.rule_create('redday_60_rule_strict', "fix_8", '<',
                                 'redday_60')

        self.manager.policy_create('system1', ['highest_20_rule',
                                               'cv_20_rule'])
        self.manager.policy_create('system2', ['highest_60_rule',
                                               'cv_60_rule'])
        self.manager.policy_create('system3', ['highest_60_rule',
                                               'cv_60_strict_rule',
                                               'redday_60_rule'])
        self.manager.policy_create('system4', ['redday_60_rule_strict'])


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
            self.log.info("%s newday" % self.name)
            self.reload()
