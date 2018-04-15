import numpy as np


def set_start_funds(dataframe, value=1000, symmetric=True):
    """sets start funds for backtesting
    """
    dataframe['USD'] = 0
    dataframe.loc[0, 'USD'] = value/2
    dataframe['BTC'] = 0
    dataframe.loc[0, 'BTC'] = value/2 / ((dataframe.loc[0, 'highest'] +
                                          dataframe.loc[0, 'lowest'])/2)


def backtest(dataframe, amount_buy=.05, amount_sell=10, delay=0,
             minfunds_USD=10, minfunds_BTC=.005, taker_fee=.003):
    """
    Args:
        amount..
            amount of currency to buy or sell for
        delay:
            #rows until order is performed
    """
    cols_required = ['USD', 'dUSD', 'BTC', 'dBTC']
    for colreq in cols_required:
        if colreq not in list(dataframe.columns):
            dataframe[colreq] = 0

    for idx, row in dataframe.iterrows():
        # BUY
        if (row['buy'] == 1 and
            amount_buy > 0 and
            dataframe.loc[idx, 'USD'] > minfunds_USD):
            # pessimistic buy for highest price in following minutes
            price = max(dataframe.loc[idx:idx+2, 'highest'])
            # or buy instantly
#            price = dataframe.loc[idx, 'highest']
            # add taker fee
            price = price * (1+taker_fee)
            if not np.isnan(price):
                if price*amount_buy > dataframe.loc[idx, 'USD']:
                    amount_buy_now = dataframe.loc[idx, 'USD'] / price
                else:
                    amount_buy_now = amount_buy
                dataframe.loc[idx, 'dUSD'] -= price*amount_buy_now
                dataframe.loc[idx, 'dBTC'] += amount_buy_now

        # SELL
        if (row['sell'] == 1 and
            amount_sell > 0 and
            dataframe.loc[idx, 'BTC'] > minfunds_BTC):
            # pessimistic buy for lowest price in following minutes
            price = min(dataframe.loc[idx:idx+2, 'lowest'])
            # or sell instantly
#            price = dataframe.loc[idx, 'lowest']
            # # add taker fee
            # price = price * (1-taker_fee)
            if not np.isnan(price):
                if amount_sell > dataframe.loc[idx, 'BTC']:
                    amount_sell_now = dataframe.loc[idx, 'BTC']
                else:
                    amount_sell_now = amount_sell
                dataframe.loc[idx, 'dUSD'] += price*amount_sell_now
                dataframe.loc[idx, 'dBTC'] -= amount_sell_now

        # UPDATE FUNDS
        if idx+1 < len(dataframe):
            dataframe.loc[idx+1, 'USD'] += (dataframe.loc[idx, 'USD'] +
                                            dataframe.loc[idx, 'dUSD'])
            dataframe.loc[idx+1, 'BTC'] += (dataframe.loc[idx, 'BTC'] +
                                            dataframe.loc[idx, 'dBTC'])


def diagnose(dataframe):
    dataframe['tot_USD'] = (dataframe['USD'] +
                            dataframe['BTC']*dataframe['lowest'])
    minprice = min(dataframe['lowest'])
    dataframe['tot_USD_cons'] = dataframe['USD'] + dataframe['BTC']*minprice
    dataframe['tot_BTC'] = (dataframe['BTC'] +
                            dataframe['USD']/dataframe['highest'])
    results = {}
    results['investment'] = dataframe.loc[0, 'tot_USD']
    results['return_on_inv_perc'] = (dataframe.loc[len(dataframe)-1,
                                                   'tot_USD'] /
                                     results['investment']-1) * 100
    dataframe['return_on_inv_perc'] = (dataframe['tot_USD'] /
                                       results['investment']-1) * 100
    dt_days = (dataframe.loc[len(dataframe)-1, 'time'] -
               dataframe.loc[0, 'time'])/1000/3600/24
    results['roi_per_day'] = ((results['return_on_inv_perc']/100+1
                               )**(1/dt_days) - 1) * 100
    results['nrbuys'] = dataframe['buy'].sum(skipna=True)
    results['nrsells'] = dataframe['sell'].sum(skipna=True)
    results['transactions'] = (dataframe['dUSD'] != 0).sum()
    buy_hold_perc = 100*(dataframe.loc[len(dataframe)-1, 'highest'] /
                         dataframe.loc[0, 'highest']-1)
    buy_hold_per_day = ((buy_hold_perc/100+1)**(1/dt_days)-1)*100
    results['buy_hold'] = buy_hold_perc
    results['vs_buy_hold'] = results['return_on_inv_perc'] - buy_hold_perc
    results['vs_buy_hold_per_day'] = results['roi_per_day'] - buy_hold_per_day
    return results
