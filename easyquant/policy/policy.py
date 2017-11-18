import copy

from datetime import datetime


class Policy(object):
    def __init__(self, name, alert=False, priority=1):
        self.rules = []
        self.name = name
        self.result = None
        self.alert = alert
        self.priority = priority

    def add_rules(self, rules):
        if not isinstance(rules, list):
            rules = [rules]

        self.rules.extend(rules)

    def filter(self, stocks):
        result = copy.deepcopy(stocks)
        for rule in self.rules:
            result = rule.filter(result)

        updated = []
        if self.result is None and result:
            updated = result.keys()
            self.result = result
            for code, data in self.result.items():
                self.insert_update_time(data)
        else:
            # insert break time to new stock only
            old_keys = set(self.result.keys())
            new_keys = set(result.keys())
            diff_keys = new_keys - old_keys
            updated = diff_keys
            for key in diff_keys:
                self.insert_update_time(result[key])
                self.result[key] = result[key]

        return {'result': self.result, 'updated': updated}

    def insert_update_time(self, stock_data):
        break_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        stock_data['update_time'] = break_time
