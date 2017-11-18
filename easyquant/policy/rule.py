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
                        data['rule_results'].update(self.indicator.get_all_val(code))
                    result[code] = data
            except KeyError:
                pass
        return result


if __name__ == "__main__":
    from easyquant.policy.indicator import ContinuousRedDaysIndicator
    from easyquant.policy.indicator import EdgeIndicator
    from easyquant.policy.indicator import StopLossIndicator
    from operator import gt, lt
    import tushare as ts
    hist = ts.get_hist_data("002597", start="2017-10-10", end="2017-11-17")
    cindicator = ContinuousRedDaysIndicator('60reddays', 2)
    eindicator = EdgeIndicator('highest', 'high')
    sindicator = StopLossIndicator('stoploss', {'002597': 31})
    cindicator.calculate("002597", hist)
    eindicator.calculate("002597", hist)
    sindicator.calculate("002597", hist)
    rule1 = Rule('rule1', lambda x: 4, lt, cindicator)
    rule2 = Rule('rule2', lambda x: x['now'], gt, eindicator)
    rule3 = Rule('rule3', lambda x: x['now'], lt, sindicator)
    results = rule1.filter({"002597": {"now": 30, "low": 25,"high": 50}})
    results = rule2.filter(results)
    results = rule3.filter(results)
    print(results)
