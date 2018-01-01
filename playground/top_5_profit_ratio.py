import tushare as ts


# current price
cp = ts.get_today_all()
# profit data
pd = ts.profit_data(top='all', year=2017)

pr_list = []

for code in cp['code']:
    try:
        # profit ratio
        if int(cp.loc[cp['code'] == code]['trade'].sum()) == 0:
            continue
        pr = pd.loc[cp['code'] == code]['divi'].sum() \
            / 10 / cp.loc[cp['code'] == code]['trade'].sum() * 100
        pr_list.append({'code': code, 'pr': pr})
    except KeyError:
        pass
    except ZeroDivisionError:
        pass

sorted_pr_list = sorted(pr_list, reverse=True, key=lambda x: x['pr'])
print(sorted_pr_list[0: 10])
