import numpy as np
import time
from datetime import datetime
from quickndirtybot.connect import get_ohlcv
from quickndirtybot.connect import concat
from quickndirtybot.io import pandize_csv


def trade(exchange, symbol, strategy, filename='trade_gdax',
          test=True, taker_fee=0.003):
    """
    strategy : dict
        'strategy' : module with measure, findbuy and findsell
        'measure_pars' : dict of kwargs for measure
        'findbuy_pars' : dict of kwargs for measure
        'findsell_pars' : dict of kwargs for measure
        'evallines' : int; how many lines of data needed to evaluate
                the current row
        'interval' : e.g. '1m'
        'minfunds_USD' : float, min funds to make transaction with
        'minfunds_BTC' : float
        'amount_buy' : float, max amount to buy
        'amount_sell' : float, max amount to sell
    """
    all_data = np.array([[]])
    i = 0
    currweek = ''
    while True:
        # manage data retrieval
        if currweek != datetime.now().strftime('%U'):
            # empty dataset after a week
            all_data = np.array([[]])
            currweek = datetime.now().strftime('%U')
        try:
            recent_data = get_ohlcv(exchange, strategy['interval'], symbol)
            recent_data = pandize_csv(recent_data)
            all_data = concat(all_data, recent_data)
        except Exception as e:
            print('timeout, going on')
            print(e)

        # measure and determine transactions
        evallines_for_strat = strategy['evallines']
        eval_data = all_data.iloc[-evallines_for_strat:, :]
        strategy['strategy'].measure(eval_data, strategy['measure_pars'])
        strategy['strategy'].findbuy(eval_data, strategy['findbuy_pars'])
        strategy['strategy'].findsell(eval_data, strategy['findsell_pars'])

        # get funds

        # act on transactions
        if test:
        # BUY
            buy_idx = list(eval_data.columns).index('buy')
            sell_idx = list(eval_data.columns).index('sell')
            hi_idx = list(eval_data.columns).index('highest')
            lo_idx = list(eval_data.columns).index('lowest')
            USD_idx = list(eval_data.columns).index('USD')
            BTC_idx = list(eval_data.columns).index('BTC')
            dUSD_idx = list(eval_data.columns).index('dUSD')
            dBTC_idx = list(eval_data.columns).index('dBTC')
            # only sell or buy decisions, not both
            if eval_data.iloc[-1, buy_idx]*eval_data.iloc[-1, sell_idx] == 0:
                if (eval_data.iloc[-1, buy_idx] == 1 and
                    eval_data.iloc[-1, USD_idx] > strategy['minfunds_USD']):
                    # do buy
                    price = eval_data.iloc[-1, hi_idx]
                    # add taker fee
                    price = price * (1+taker_fee)
                    if not np.isnan(price):
                        if (price*strategy['amount_buy'] >
                            eval_data.iloc[-1, USD_idx]):
                            amount_buy_now = eval_data.iloc[-1, USD_idx] / price
                        else:
                            amount_buy_now = strategy['amount_buy']
                        eval_data.iloc[-1, dUSD_idx] -= price*amount_buy_now
                        eval_data.iloc[-1, dBTC_idx] += amount_buy_now
                if (eval_data.iloc[-1, sell_idx] == 1 and
                    eval_data.iloc[-1, BTC_idx] > strategy['minfunds_BTC']):
                    # do sell
                    price = eval_data.iloc[-1, lo_idx]
                    if not np.isnan(price):
                        if strategy['amount_sell'] > eval_data.iloc[-1, BTC_idx]:
                            amount_sell_now = eval_data.iloc[-1, BTC_idx]
                        else:
                            amount_sell_now = strategy['amount_sell']
                        eval_data.iloc[-1, dUSD_idx] += price*amount_sell_now
                        eval_data.iloc[-1, dBTC_idx] -= amount_sell_now
        else:
            buy_idx = list(eval_data.columns).index('buy')
            sell_idx = list(eval_data.columns).index('sell')
            USD_idx = list(eval_data.columns).index('USD_true')
            BTC_idx = list(eval_data.columns).index('BTC_true')
            # only sell or buy decisions, not both
            if eval_data.iloc[-1, buy_idx]*eval_data.iloc[-1, sell_idx] == 0:
                if (eval_data.iloc[-1, buy_idx] == 1 and
                    eval_data.iloc[-1, USD_idx] > strategy['minfunds_USD']):
                    print('real trading not implemented yet')
                if (eval_data.iloc[-1, sell_idx] == 1 and
                    eval_data.iloc[-1, BTC_idx] > strategy['minfunds_BTC']):
                    # do sell
                    print('real trading not implemented yet')

        # concatenate data (with all new columns)
        all_data = all_data.iloc[:-3, :]
        all_data = all_data.append(eval_data.iloc[-3:, :], ignore_index=True)

        # save
        all_data.to_excel(filename + '_' +
                          datetime.now().strftime('%Y-%U') +
                          '.xlsx')

        # wait and go for next loop
        i += 1
        time.sleep(30)  # every half interval
