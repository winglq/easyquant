import json
import os

from datetime import datetime
from easyquant import exceptions
from easyquant.easydealutils import time as etime


class Indicator(object):
    def __init__(self, name):
        self.results = {}
        self.name = name

    def calculate(self, code, dataframe):
        self.validate(code, dataframe)
        self.cal(code, dataframe)
        print("Indicator: %s Code: %s init completed" %
              (self.name, code))

    def validate(self, code, dataframe):
        pass

    def cal(self, code, dataframe):
        raise NotImplementedError()

    def get_compare_val(self, code):
        raise NotImplementedError()

    def get_all_val(self, code):
        return self.results[code]

    def save(self):
        with open(self.get_save_location(), "w") as f:
            json.dump(self.results, f, indent=2)

    def load(self):
        print("Indicator %s loading %s" %
              (self.name, self.get_save_location()))
        with open(self.get_save_location()) as f:
            self.results = json.load(f)

    def get_save_location(self):
        fmt_time = datetime.now().strftime("%y%m%d")
        return "%s_%s.json" % (fmt_time, self.name)


class IndicatorInDays(Indicator):
    def __init__(self, name, days):
        super(IndicatorInDays, self).__init__(name)
        self.days = days

    def validate(self, code, dataframe):
        if dataframe is None:
            raise exceptions.NoHistoryData(
                "%s Indicator(%s) has no history data" % code)
        if len(dataframe) < self.days:
            raise exceptions.LessDaysThanExpected(
                "%s Indicator: %s expect days: %s actual "
                "days %s" % (code, self.name, self.days,
                             len(dataframe)))

    def calculate(self, code, dataframe):
        self.validate(code, dataframe)
        self.cal(code, dataframe[0: self.days])
        print("Indicator: %s Code: %s init completed" %
              (self.name, code))

    def get_save_location(self):
        fmt_time = datetime.now().strftime("%y%m%d")
        return "%s_%s_%sdays.json" % (fmt_time, self.name, self.days)


class CVIndicator(IndicatorInDays):
    def __init__(self, name, column, days=20):
        super(CVIndicator, self).__init__(name, days)
        self.days = days
        self.column = column

    def cal(self, code, dataframe):
        std = dataframe[self.column].std()
        mean = dataframe[self.column].mean()
        cv = std / mean * 100
        self.results[code] = {'cv': round(float(cv), 2)}

    def get_compare_val(self, code):
        return self.results[code]['cv']


class EdgeIndicator(IndicatorInDays):

    def __init__(self, name, column, days=30):
        super(EdgeIndicator, self).__init__(name, days)
        self.column = column
        self.compare_key = "%s_edge" % column
        self.days = days

    def cal(self, code, dataframe):
        idx = dataframe[0: self.days][self.column].idxmax()
        val = dataframe[0: self.days][self.column][idx]
        self.results[code] = {'%s_date' % self.compare_key: idx,
                              self.compare_key: round(float(val), 2)}

    def get_compare_val(self, code):
        return self.results[code][self.compare_key]


class ContinuousRedDaysIndicator(IndicatorInDays):
    def __init__(self, name, expected_continuous_days, days=60):
        super(ContinuousRedDaysIndicator, self).__init__(name, days)
        self.expected_continuous_days = expected_continuous_days

    def is_red_day(self, series):
        return series['close'] > series['open']

    def cal(self, code, dataframe):
        continuous_reddays = 0
        count = 0
        for index, row in dataframe.iterrows():
            if self.is_red_day(row):
                continuous_reddays += 1
            else:
                if continuous_reddays >= self.expected_continuous_days:
                    count += 1
                continuous_reddays = 0
        self.results[code] = {'continuous_reddays_count': count}

    def get_compare_val(self, code):
        return self.results[code]['continuous_reddays_count']

    def get_save_location(self):
        fmt_time = datetime.now().strftime("%y%m%d")
        return "%s_%s_%sdays_%scdays.json" % (fmt_time, self.name, self.days,
                                              self.expected_continuous_days)


class StopLossIndicator(Indicator):

    def __init__(self, name, code_stoplossprice_dict):
        super(StopLossIndicator, self).__init__(name)
        self.code_stoplossprice_dict = code_stoplossprice_dict

    def cal(self, code, dataframe):
        if code in self.code_stoplossprice_dict:
            self.results[code] = {'stop_loss_price':
                                  self.code_stoplossprice_dict[code]}

    def get_compare_val(self, code):
        return self.results[code]['stop_loss_price']


class YesterdayUpDownStockCount(IndicatorInDays):
    def __init__(self, name):
        super(YesterdayUpDownStockCount, self).__init__(name, 1)
        self.previous_trade_day = etime.previous_trade_date_from_now(1)
        self.results['total'] = {}
        self.results['total']['yesterday_nochange'] = 0
        self.results['total']['yesterday_up'] = 0
        self.results['total']['yesterday_down'] = 0

    def yesterday_change(self, series):
        return series['close'] - series['open']

    def cal(self, code, dataframe):
        yesterday = self.previous_trade_day.strftime("%Y-%m-%d")
        if yesterday != dataframe.index[0]:
            self.results['total']['yesterday_nochange'] += 1
            return

        yesterday_series = dataframe.loc[dataframe.index[0]]
        change = self.yesterday_change(yesterday_series)
        if change > 0:
            self.results['total']['yesterday_up'] += 1
        if change < 0:
            self.results['total']['yesterday_down'] += 1
        if change == 0:
            self.results['total']['yesterday_nochange'] += 1


if __name__ == "__main__":
    import tushare as ts
    hist = ts.get_hist_data("002597", start="2017-09-10", end="2017-11-17")
    hindicator = EdgeIndicator('edge', 'close', 30)
    yindicator = YesterdayUpDownStockCount('yesterday')
    hindicator.calculate("002597", hist)
    print(hindicator.get_all_val("002597"))
    cindicator = ContinuousRedDaysIndicator('reddays', 3, 30)
    cindicator.calculate('002597', hist)
    print(cindicator.get_all_val("002597"))
    yindicator.calculate('002597', hist)
    print(yindicator.get_all_val('total'))
