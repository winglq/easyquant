import tushare as ts
import os
import json
import functools

from datetime import datetime, timedelta
from easyquant.exceptions import NoHistoryData
from eventlet.greenpool import GreenPool
from easyquotation.helpers import get_stock_codes, stock_code_path
from easyquant.easydealutils import time as etime

hist_cache = {}

all_codes_cache = None

def get_all_stock_codes(update=False):
    global all_codes_cache
    if all_codes_cache is None or update:
        bs = ts.get_stock_basics()
        all_codes_cache = bs.index.tolist()
        all_codes_cache.sort()
    return all_codes_cache


def get_edge_during_days(stock, start, end, coloumn, highest=True):
    """get the edge value from start to end.
    **params stock:** stock id
    **params start:** start date. datetime type
    **params end:** end date. datetime type
    **params coloumn:** the coloumn of DataFrame, eg. 'high', 'now'...
    **params highest:** True get the hight edge, False get lowest edge"""
    strstart = start.strftime('%Y-%m-%d')
    strend = end.strftime('%Y-%m-%d')
    key = "%s:%s:%s" % (strstart, strend, stock)
    if key not in hist_cache:
        hist = ts.get_hist_data(stock, start=strstart, end=strend)
        hist_cache[key] = hist
        if hist is None:
            raise NoHistoryData("Could not get history data for stock %s" %
                                stock)
    if highest:
        idxmax = hist_cache[key][coloumn].idxmax()
        max_val = hist_cache[key][coloumn][idxmax]
        std = hist_cache[key][coloumn].std()
        mean = hist_cache[key][coloumn].mean()
        return {'max': max_val,
                'idxmax': idxmax,
                'cv': std / mean * 100}
    else:
        idxmin = hist_cache[key][coloumn].idxmin()
        min_val = hist_cache[key][coloumn][idxmin]
        std = hist_cache[key][coloumn].std()
        mean = hist_cache[key][coloumn].mean()
        return {'min': min_val,
                'idxmin': idxmin,
                'cv': std / mean * 100}


def get_edge_during_previous_days(stock, days, coloumn, highest=True):
    start = etime.previous_trade_date_from_now(days)
    end = datetime.now() - timedelta(days=1)
    return get_edge_during_days(stock, start, end, coloumn, highest)


def eventlet_handle(fun, stock_code, ret_dict):
    try:
        val = fun(stock_code)
        print(stock_code + " completed max %0.2f" % val['max'])
        ret_dict[stock_code] = val
    except ValueError:
        print(stock_code + " get history failed")
    except NoHistoryData:
        print(stock_code + " get history failed")


def get_all_highest_druing_previous_days(days, result):
    stock_codes = get_stock_codes()
    gp = GreenPool()
    today = datetime.now().strftime("%Y-%m-%d")
    filename = "%s_highest_%s_days.json" % (today, days)
    if os.path.exists(filename):
        with open(filename) as f:
            result.update(json.load(f))
            return
    for stock in stock_codes:
        gp.spawn(eventlet_handle, functools.partial(
            get_edge_during_previous_days, coloumn='high',
            days=days, highest=True),
                 stock, result)
    gp.waitall()
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    result = {}
    print(get_edge_during_previous_days('000008', 20, 'high', highest=True))
