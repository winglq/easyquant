import tushare as ts
import requests
import json
import time
from eventlet.greenpool import GreenPool
from datetime import datetime, timedelta
from easyquant import StrategyTemplate
from easyquant.policy.manager import Manager
from easyquant.easydealutils.time import previous_trade_date_from_now
from easyquant.utils.utils import get_all_stock_codes
from oslo_config import cfg
from datetime import datetime

opts = [
    cfg.StrOpt("alert_post_url",
               help="alert post url"),
    cfg.StrOpt("policy_post_url",
               help="Policy post url"),
    cfg.StrOpt("stock_owner_username",
               help="Username used to get stocks for stop loss indicator"),
    cfg.StrOpt("stock_owner_password",
               help="Password used to get stocks for stop loss indicator"),
    cfg.StrOpt("login_url",
               help="login url to get stocks"),
    cfg.StrOpt("query_stocks_url",
               help="query url to get stocks"),
    cfg.StrOpt("query_stocks_url",
               help="query url to get stocks"),
    cfg.StrOpt("statistics_post_url",
               help="statistics post url"),
]

CONF = cfg.CONF
CONF.register_opts(opts)

class Strategy(StrategyTemplate):

    def __init__(self, user, log_handler, main_engine):
        super(Strategy, self).__init__(user, log_handler, main_engine)
        self.manager = Manager()
        self.define_indicators()
        self.define_get_val_funcs()
        self.define_rules()
        self.define_policies()
        self.policy_post_url = CONF.policy_post_url
        self.alert_post_url = CONF.alert_post_url
        self.statistics_post_url = CONF.statistics_post_url
        self.priority = 1

    def get_stocks_for_stop_loss_indicator(self):
        while True:
            try:
                s = requests.Session()
                # first login
                s.post(CONF.login_url, data={'user': CONF.stock_owner_username,
                                             'password':
                                             CONF.stock_owner_password})
                r = s.get(CONF.query_stocks_url)
                break
            except Exception as e:
                print("Error: %s" % str(e))
                time.sleep(60)

        # query stocks
        if r.status_code == 500:
            return []
        return json.loads(r.text)

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
            self.log.info("All indicators loaded successfully")
            return
        self.manager.reset()
        self.create_stop_loss_price_indicator()
        self.define_user_stocks_rule()
        start_time = datetime.now()
        stock_codes = get_all_stock_codes(True)
        gp = GreenPool()
        for code in stock_codes:
            if code[0: 2] not in ['00', '60', '30']:
                continue
            gp.spawn(self.manager.prepare,
                     code, Strategy.get_hist_data)
        gp.waitall()
        self.manager.save()
        self.log.info("rub_before_strategy completed. Start from %s"
                      % start_time.strftime("%Y-%m-%d %H:%M"))

    def strategy(self, event):
        result = self.manager.run(event.data)
        updated = False
        for policy, data in result.items():
            if data['updated'] and self.policy_post_url:
                updated = True
            if self.manager.get_policy(policy).alert and \
                    data['updated']:
                alert_contents = []
                for key in data['updated']:
                    data['result'][key]['code'] = key
                    alert_contents.append(data['result'][key])
                action = "sell" if policy in \
                    ["stoploss", "sell_when_ma20btnow" ] else "buy"
                send_data = {'type': 'stock',
                             'priority':
                             self.manager.get_policy(policy).priority,
                             'data': {'stocks': alert_contents,
                                      'action': action,
                                      'system': policy}}
                self.log.info("New alert for policy %s" % policy)

                requests.post(self.alert_post_url,
                              json = send_data)
            data.pop('updated')

        if updated:
            requests.post(self.policy_post_url,
                          json = result)

    def define_indicators(self):
        self.manager.indicator_create('edge_cls', name='highest_20',
                                      column='high', days=20)
        self.manager.indicator_create('edge_cls', name='highest_30',
                                      column='high', days=30)
        self.manager.indicator_create('edge_cls', name='highest_60',
                                      column='high', days=60)
        self.manager.indicator_create('cv_cls', name='cv_20', column='close',
                                      days=20)
        self.manager.indicator_create('cv_cls', name='cv_60', column='close',
                                      days=60)

        self.manager.indicator_create("continuouse_red_days_cls",
                                      name='redday_60',
                                      expected_continuous_days=5,
                                      days=60)
        self.manager.indicator_create("yesterday_updown_stock_count_cls",
                                      name='updown')
        self.manager.indicator_create("today_updown_stock_count_cls",
                                      name='today_updown')
        self.manager.indicator_create("continuous_big_red_days_cls",
                                      expected_continuous_days=4,
                                      name='big_redday_60')

        self.create_stop_loss_price_indicator()
        self.manager.indicator_create(
            "latest_trade_day_ma20_less_than_ma5_cls",
            name='ma20ltma5')
        self.manager.indicator_create(
            "latest_trade_day_ma20_cls",
            name='ma20')

    def create_stop_loss_price_indicator(self):
        stocks = self.get_stocks_for_stop_loss_indicator()
        code_price_dict = {}
        for stock in stocks:
            code_price_dict[stock["code"]] = stock["stop_loss_price"]
        self.log.info("Creating stop loss price indicator for "
                      "stocks: %s" % code_price_dict)
        self.manager.indicator_create("stop_loss_price_cls",
                                      name='stoploss',
                                      code_stoplossprice_dict=code_price_dict)

    def define_get_val_funcs(self):
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_500',
                                         500)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_2',
                                         2)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_1',
                                         1)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_8',
                                         8)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_10',
                                         10)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_30',
                                         30)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_True',
                                         True)
        self.manager.get_val_func_create('get_fixed_value_func', 'fix_False',
                                         False)
        self.manager.get_val_func_create('get_value_by_key_func', 'key_now',
                                         'now')
        self.manager.get_val_func_create('get_value_by_key_ignore_zero_func',
                                         'key_now_ignore_zero',
                                         'now')

    def define_user_stocks_rule(self):
        stocks = self.get_stocks_for_stop_loss_indicator()
        codes = [s["code"] for s in stocks]
        self.manager.selectedcodesrule_create('user_stocks_rule', codes)

    def define_rules(self):
        self.manager.rule_create('highest_20_rule', "key_now", '>',
                                 'highest_20')
        self.manager.rule_create('highest_60_rule', "key_now", '>',
                                 'highest_60')
        self.manager.rule_create('highest_30_rule', "key_now", '>',
                                 'highest_30')
        self.manager.rule_create('cv_20_rule', "fix_500", '>',
                                 'cv_20')
        self.manager.rule_create('cv_20_strict_rule', "fix_2", '>',
                                 'cv_20')
        self.manager.rule_create('cv_60_rule', "fix_500", '>',
                                 'cv_60')
        self.manager.rule_create('cv_60_strict_rule', "fix_2", '>',
                                 'cv_60')
        self.manager.rule_create('cv_60_lt_10_rule', "fix_10", '>',
                                 'cv_60')
        self.manager.rule_create('redday_60_rule', "fix_1", '<',
                                 'redday_60')
        self.manager.rule_create('big_redday_60_rule', "fix_1", '<',
                                 'big_redday_60')

        self.manager.rule_create('stop_loss_price_rule', "key_now_ignore_zero",
                                 '<', 'stoploss')
        self.manager.rule_create('today_updown_stocks_rule', "fix_30",
                                 '<', 'today_updown')
        self.manager.rule_create('ma20ltma5_true_rule',
                                 'fix_True', '=', 'ma20ltma5')
        self.manager.rule_create('ma20ltma5_false_rule',
                                 'fix_False', '=', 'ma20ltma5')
        self.manager.rule_create('now_lt_ma20_rule',
                                 'key_now', '<', 'ma20')

        self.define_user_stocks_rule()


    def define_policies(self):

        self.manager.policy_create('system1-500cv',
                                   ['highest_20_rule',
                                    'today_updown_stocks_rule',
                                    'cv_20_rule'])

        self.manager.policy_create('system2-500cv',
                                   ['highest_60_rule',
                                    'today_updown_stocks_rule',
                                    'cv_60_rule'])

        self.manager.policy_create('system1-2cv', ['highest_20_rule',
                                                   'cv_20_strict_rule',
                                                   'ma20ltma5_true_rule',
                                                   'today_updown_stocks_rule'],
                                   alert=True)

        self.manager.policy_create('system2-2cv', ['highest_60_rule',
                                                   'cv_60_strict_rule',
                                                   'ma20ltma5_true_rule',
                                                   'today_updown_stocks_rule'],
                                   alert=True, priority=2)

        self.manager.policy_create('fjj', ['redday_60_rule'])
        self.manager.policy_create('stoploss', ['stop_loss_price_rule'],
                                   alert=True, priority=2)
        self.manager.policy_create('sell_when_ma20btnow',
                                   ['user_stocks_rule',
                                    'now_lt_ma20_rule'],
                                   alert=True, priority=2)

        self.manager.policy_create('bigreddays-10cv-30break',
                                   ['highest_30_rule',
                                    'cv_60_lt_10_rule',
                                    'big_redday_60_rule',
                                    'ma20ltma5_true_rule',
                                    'today_updown_stocks_rule'],
                                   alert=True, priority=1)

    def push_statistics(self):
        try:
            result = self.manager.get_indicator_results("today_updown",
                                                        'market')
            send_data={'update_time': datetime.now().strftime("%m-%d %H:%M")}
            send_data["today_updown"] = result
            requests.post(self.statistics_post_url,
                          json=send_data)
        except Exception:
            self.log.info("push statistics error")

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
            self.push_statistics()
        elif event.data.clock_event == 30:
            self.log.info("30分钟")
        elif event.data.clock_event == 'newday':
            self.log.info("%s newday" % self.name)
            self.reload()

    def shutdown(self):
        """
        关闭进程前调用该函数
        :return:
        """
        if self._initing:
            self.manager.save()
