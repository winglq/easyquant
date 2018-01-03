import tushare as ts

from datetime import datetime as dt


# current price
cp = ts.get_today_all()
# profit data

year = dt.now().year
previous_year = year - 1
year_before_previous_year = previous_year - 1
pd_ybpy = ts.profit_data(top='all', year=year_before_previous_year)
pd_py = ts.profit_data(top='all', year=previous_year)
pd_current = 
pd = ts.profit_data(top='all', year=2016)
#pd = ts.profit_data(top='all', year=2017)

pr_list = []

for code in cp['code']:
    try:
        # profit ratio
        if int(cp.loc[cp['code'] == code]['trade'].sum()) == 0:
            continue
        shares = pd.loc[pd['code'] == code]['shares'].sum()
        pr = pd.loc[pd['code'] == code]['divi'].sum() \
            / (10 + shares) / cp.loc[cp['code'] == code]['trade'].sum() * 100
        pr_list.append({'code': code, 'pr': pr,
                        'data': pd.loc[pd['code'] == code].\
                        to_csv(header=None,
                               index=False)})
    except KeyError:
        pass
    except ZeroDivisionError:
        pass

sorted_pr_list = sorted(pr_list, reverse=True, key=lambda x: x['pr'])
print(sorted_pr_list[0: 10])
