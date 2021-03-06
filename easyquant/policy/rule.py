import copy
import json
from easyquant import exceptions
from easyquant.policy.indicator import RealTimeIndicator
from playground.top_5_profit_ratio import get_top_5_profit_ratio_stocks


class Rule(object):
    def __init__(self, name, get_val_func, operator, indicator):
        self.name = name
        self.indicator = indicator
        self.operator = operator
        self.get_val_func = get_val_func

    def filter(self, stocks):
        result = {}
        for code, data in stocks.items():
            try:
                if self.operator(self.get_val_func(data),
                                 self.indicator.get_compare_val(code)):
                    if not data.get('rule_results', None):
                        data['rule_results'] = self.indicator.get_all_val(code)
                    else:
                        data['rule_results'].update(
                            self.indicator.get_all_val(code))
                    result[code] = data
            except KeyError:
                pass
            except exceptions.StockValueZero:
                pass
        return result


class SelectedCodesRule(Rule):
    def __init__(self, name, codes):
        super(SelectedCodesRule, self).__init__(name, None, None, None)
        self.codes = codes

    def filter(self, stocks):
        result = {}
        for code, data in stocks.items():
            if code in self.codes:
                result[code] = data
        return result

class TopProfitRatioRule(Rule):
    def __init__(self, name):
        super(TopProfitRatioRule, self).__init__(name, None, None, None)
        self.top_5_stocks = get_top_5_profit_ratio_stocks()

    def filter(self, stocks):
        result = {}
        top_5_codes = [x['code'] for x in self.top_5_stocks]
        for code, data in stocks.items():
            if code in top_5_codes:
                for x in self.top_5_stocks:
                    if code == x['code']:
                        rule_result = copy.deepcopy(x)
                        rule_result.pop('code')
                        rule_result.pop('price')
                        rdata = json.loads(rule_result.pop('data'))
                        rule_result['report_date'] = \
                            list(rdata['report_date'].values())
                        rule_result['shares'] = \
                            list(rdata['shares'].values())
                        rule_result['divi'] = \
                            list(rdata['divi'].values())
                        data['rule_results'] = rule_result
                result[code] = data
        return result


if __name__ == "__main__":
    from easyquant.policy.indicator import ContinuousRedDaysIndicator
    from easyquant.policy.indicator import EdgeIndicator
    from easyquant.policy.indicator import StopLossIndicator
    from operator import gt, lt
    import tushare as ts
    hist = ts.get_hist_data("002597", start="2017-10-10", end="2017-11-17")
    cindicator = ContinuousRedDaysIndicator('60reddays', 2, 10)
    eindicator = EdgeIndicator('highest', 'high', 10)
    sindicator = StopLossIndicator('stoploss', {'002597': 31})
    cindicator.calculate("002597", hist)
    eindicator.calculate("002597", hist)
    hist["002597"] = 0.0
    sindicator.calculate("002597", hist)
    rule1 = Rule('rule1', lambda x: 4, lt, cindicator)
    rule2 = Rule('rule2', lambda x: x['now'], gt, eindicator)
    rule3 = Rule('rule3', lambda x: x['now'], lt, sindicator)
    results = rule1.filter({"002597": {"now": 30, "low": 25,"high": 50}})
    results = rule2.filter(results)
    results = rule3.filter(results)
    print(results)
