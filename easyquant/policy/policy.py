import copy

from datetime import datetime


class Policy(object):
    def __init__(self, name):
        self.rules = []
        self.name = name
        self.result = None

    def add_rules(self, rules):
        if not isinstance(rules, list):
            rules = [rules]

        self.rules.extend(rules)

    def filter(self, stocks):
        result = copy.deepcopy(stocks)
        for rule in self.rules:
            result = rule.filter(result)

        updated = False
        if self.result is None and result:
            updated = True
            self.result = result
            for code, data in self.result.items():
                self.insert_break_time(data)
        else:
            # insert break time to new stock only
            old_keys = set(self.result.keys())
            new_keys = set(result.keys())
            diff_keys = new_keys - old_keys
            updated = True if len(diff_keys) else False
            for key in diff_keys:
                self.insert_break_time(result[key])
                self.result[key] = result[key]

        return {'result': self.result, 'updated': updated}

    def insert_break_time(self, stock_data):
        break_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        stock_data['break_time'] = break_time
