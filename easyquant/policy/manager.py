import pandas

from easyquant.policy.policy import Policy
from easyquant import exceptions
from operator import eq, lt, gt
from easyquant.policy.indicator import ContinuousRedDaysIndicator
from easyquant.policy.indicator import EdgeIndicator
from easyquant.policy.indicator import StopLossIndicator
from easyquant.policy.indicator import CVIndicator
from easyquant.policy.indicator import YesterdayUpDownStockCount
from easyquant.policy.indicator import RealTimeIndicator
from easyquant.policy.indicator import TodayUpDownStockCount
from easyquant.policy.rule import Rule


class Manager(object):

    def __init__(self):
        self.indicators = {}
        self.indicator_classes = {}
        self.operators = {}
        self.rules = {}
        self.get_val_funcs = {}
        self.get_val_func_wrappers = {}
        self.polices = []

        self.init_internal_operators()
        self.init_inertnal_get_left_val_funcs()
        self.init_internal_indicator_classes()
        self.preparing = False
        self.prepared = False

    def init_inertnal_get_left_val_funcs(self):

        def get_fixed_value_wrapper(val):
            return lambda x: val

        def get_value_by_key_wrapper(key):
            return lambda x: x[key]

        def get_value_by_key_ignore_zero_wrapper(key):
            def get_value_by_key_ignore_zero(stock):
                if int(stock[key]) != 0:
                    return stock[key]
                else:
                    raise exceptions.StockValueZero()
            return get_value_by_key_ignore_zero

        self.get_val_func_wrappers = \
            {'get_fixed_value_func': get_fixed_value_wrapper,
             'get_value_by_key_func': get_value_by_key_wrapper,
             'get_value_by_key_ignore_zero_func':
             get_value_by_key_ignore_zero_wrapper}

    def init_internal_operators(self):
        oper_maps = {'>': gt,
                     '<': lt,
                     '=': eq}
        for name, op in oper_maps.items():
            self.register_operators(name, op)

    def init_internal_indicator_classes(self):
        reddays_5 = ContinuousRedDaysIndicator('5_continuous_reddays',
                                               5, 60)
        highest = EdgeIndicator('highest', 'high')
        indicator_map = {"continuouse_red_days_cls": ContinuousRedDaysIndicator,
                         "edge_cls": EdgeIndicator,
                         "stop_loss_price_cls": StopLossIndicator,
                         "cv_cls": CVIndicator,
                         "yesterday_updown_stock_count_cls":
                         YesterdayUpDownStockCount,
                         "today_updown_stock_count_cls":
                         TodayUpDownStockCount}
        for name, indicator in indicator_map.items():
            self.register_indicator_cls(name, indicator)

    def register_indicator_cls(self, name, indicator_cls):
        self.indicator_classes[name] = indicator_cls

    def register_indicator(self, name, indicator):
        self.indicators[name] = indicator

    def register_operators(self, name, operator):
        self.operators[name] = operator

    def register_rules(self, name, rule):
        self.rules[name] = rule

    def policy_create(self, name, rules, **kwargs):
        if not isinstance(rules, list):
            rules = [rules]
        policy = Policy(name, **kwargs)
        # rule names to rule objects
        rules = [self.rules[rule] for rule in rules]
        policy.add_rules(rules)
        self.polices.append(policy)

    def get_policy(self, name):
        return next(filter(lambda x: x.name == name, self.polices))

    def get_val_func_create(self, wrapper_name, name, *args):
        self.get_val_funcs[name] = \
            self.get_val_func_wrappers[wrapper_name](*args)

    def rule_create(self, name, get_val_func, operator, indicator):
        indicator_obj = self.indicators[indicator]
        operator_obj = self.operators[operator]
        rule = Rule(name, self.get_val_funcs[get_val_func],
                    operator_obj, indicator_obj)
        self.register_rules(rule.name, rule)

    def indicator_create(self, indicator_cls_key, **kwargs):
        cls = self.indicator_classes[indicator_cls_key]
        indicator = cls(**kwargs)
        self.register_indicator(indicator.name, indicator)

    def get_rule(self, name):
        return self.rules[name]

    def run(self, stocks):
        result = {}
        self.prepare_realtime(stocks)
        for policy in self.polices:
            result[policy.name] = policy.filter(stocks)
        return result

    def reset(self):
        for policy in self.polices:
            policy.reset()

    def load_indicators(self):
        try:
            for name, indicator in self.indicators.items():
                indicator.load()
        except FileNotFoundError:
            return False
        return True

    def prepare(self, code, get_dataframe_func):
        for name, indicator in self.indicators.items():
            try:
                indicator.calculate(code, get_dataframe_func(code))
            except exceptions.LessDaysThanExpected as e:
                print(str(e))
            except exceptions.NoHistoryData as e:
                print(str(e))

    def prepare_realtime(self, stocks):
        stocks_frame = None
        for name, indicator in self.indicators.items():
            if isinstance(indicator, RealTimeIndicator):
                if stocks_frame is None:
                    stocks_frame = pandas.DataFrame.from_dict(stocks).T
                indicator.calculate_realtime(stocks_frame)

    def get_indicator_results(self, indicator, code):
        return self.indicators[indicator].get_all_val(code)

    def save(self):
        for name, indicator in self.indicators.items():
            indicator.save()


if __name__ == "__main__":
    import tushare as ts
    manager = Manager()
    manager.indicator_create('edge_cls', name='highest', column='high', days=20)
    manager.indicator_create('cv_cls', name='20dayscv', column='close', days=20)
    manager.rule_create('highest_rule', lambda x: x['high'], '>', 'highest')
    manager.rule_create('20dayscv_rule', lambda x: 2, '>', '20dayscv')
    policy = manager.policy_create("policy1", ["highest_rule", "20dayscv_rule"])
    manager.prepare("603609", lambda x: ts.get_hist_data(x,
                                                         start="2017-08-10",
                                                         end="2017-11-17"))
    manager.save()
    print(manager.run({"603609": {"now": 30, "low": 25,"high": 50}}))
