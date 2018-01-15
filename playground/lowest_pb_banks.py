import tushare as ts

basic = ts.get_stock_basics()
lowest_pb_banks = basic.sort_values('pb').loc[basic['pb']>0] \
    [basic['industry']=='银行'].iloc[0:10][['name', 'pb']]
print(lowest_pb_banks)


