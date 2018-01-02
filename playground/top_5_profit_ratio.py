import tushare as ts
import easyquotation
import csv

from datetime import datetime as dt

source = easyquotation.use('sina')
# current price
cp = source.all
# profit data

year = dt.now().year
previous_year = year - 1
year_before_previous_year = previous_year - 1
pd_ybpy = ts.profit_data(top='all', year=year_before_previous_year)
pd_py = ts.profit_data(top='all', year=previous_year)

pr_list = []


def _cal_profit_ratio(code, price, profit_data):
    try:
        pds = profit_data[profit_data['code'] == code]
        total_divis_per_share = 0
        if len(pds) == 0:
            return 0, None
        for pd in pds.iterrows():
            shares = pd[1]['shares']
            divis = pd[1]['divi']
            divis_per_share = divis / (10 + shares)
            total_divis_per_share += divis_per_share
        return total_divis_per_share / price * 100, pds.to_json()
    except KeyError:
        return 0, None
    except ZeroDivisionError:
        return 0, None

def cal_profit_ratio(code, price, pd_previous_year,
                     pd_year_before_previous_year):
    if dt.now().month > 7:
        return _cal_profit_ratio(code, price, pd_previous_year)
    else:
        pds = pd_previous_year[pd_previous_year['code'] == code]
        if len(pds) > 0:
            for pd in pds.iterrows():
                report_year = int(pd[1]['report_date'].split('-')[0])

                if report_year == dt.now().year:
                    break
            else:
                return _cal_profit_ratio(code, price,
                                         pd_year_before_previous_year)

            return _cal_profit_ratio(code, price, pd_previous_year)
        else:
            return _cal_profit_ratio(code, price, pd_year_before_previous_year)


def get_top_5_profit_ratio_stocks():
    for code, data in cp.items():
        if int(data['now']) == 0:
            continue
        price = data['now']
        pr, data = cal_profit_ratio(code, price, pd_py, pd_ybpy)
        pr_list.append({'code': code, 'pr': pr, 'price': price, 'data': data})
    
    sorted_pr_list = sorted(pr_list, reverse=True, key=lambda x: x['pr'])
    return sorted_pr_list[0: 5]


if __name__ == "__main__":
    print(get_top_5_profit_ratio_stocks())
