import numpy as np
import time
from datetime import datetime
from quickndirtybot.connect import get_ohlcv, concat, get_funds, get_orderbook_now
from quickndirtybot.io import pandize_csv


def trade(exchange, symbol, strategy_dict, filename='trade_gdax',
          test=True, taker_fee=0.003):
    """
    strategy_dict : dict
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
            print('new week. starting new dataset')
            all_data = np.array([[]])
            currweek = datetime.now().strftime('%U')
        # try:
        recent_data = get_ohlcv(exchange, strategy_dict['interval'], symbol)
        recent_data = pandize_csv(recent_data)
        all_data = concat(all_data, recent_data)
        # except Exception as e:
        #     print('timeout, going on')
        #     print(e)

        # measure and determine transactions
        evallines_for_strat = strategy_dict['evallines']
        eval_data = all_data.iloc[-evallines_for_strat:, :].copy()
        strategy_dict['strategy'].measure(eval_data, **strategy_dict['measure_pars'])
        strategy_dict['strategy'].findbuy(eval_data, **strategy_dict['findbuy_pars'])
        strategy_dict['strategy'].findsell(eval_data, **strategy_dict['findsell_pars'])

        # get funds
        if not test or i == 0:
            colnames = list(eval_data.columns)
            if 'USD' not in colnames:
                eval_data['USD'] = 0
            USD_idx = list(eval_data.columns).index('USD')
            if 'BTC' not in colnames:
                eval_data['BTC'] = 0
            BTC_idx = list(eval_data.columns).index('BTC')
            funds = get_funds(exchange, ['EUR', 'BTC'])
            eval_data.iloc[-1, USD_idx] = funds['EUR']
            eval_data.iloc[-1, BTC_idx] = funds['BTC']
        else:
            colnames = list(eval_data.columns)
            if 'USD' not in colnames:
                eval_data['USD'] = 0
            USD_idx = list(eval_data.columns).index('USD')
            if 'BTC' not in colnames:
                eval_data['BTC'] = 0
            BTC_idx = list(eval_data.columns).index('BTC')
            if 'dUSD' not in colnames:
                eval_data['dUSD'] = 0
            dUSD_idx = list(eval_data.columns).index('dUSD')
            if 'dBTC' not in colnames:
                eval_data['dBTC'] = 0
            dBTC_idx = list(eval_data.columns).index('dBTC')
            dUSD = eval_data.iloc[-2, dUSD_idx]
            if np.isnan(dUSD):
                eval_data.iloc[-1, USD_idx] = (eval_data.iloc[-2, USD_idx])
            else:
                eval_data.iloc[-1, USD_idx] = (eval_data.iloc[-2, USD_idx] +
                                               dUSD)
            dBTC = eval_data.iloc[-2, dBTC_idx]
            if np.isnan(dBTC):
                eval_data.iloc[-1, BTC_idx] = (eval_data.iloc[-2, BTC_idx])
            else:
                eval_data.iloc[-1, BTC_idx] = (eval_data.iloc[-2, BTC_idx] +
                                               dBTC)

        # act on transactions
        if test:
            # BUY
            if 'buy' not in colnames:
                eval_data['buy'] = 0
            buy_idx = list(eval_data.columns).index('buy')
            if 'sell' not in colnames:
                eval_data['sell'] = 0
            sell_idx = list(eval_data.columns).index('sell')
            if 'highest' not in colnames:
                eval_data['highest'] = 0
            hi_idx = list(eval_data.columns).index('highest')
            if 'lowest' not in colnames:
                eval_data['lowest'] = 0
            lo_idx = list(eval_data.columns).index('lowest')
            if 'dUSD' not in colnames:
                eval_data['dUSD'] = 0
            dUSD_idx = list(eval_data.columns).index('dUSD')
            if 'dBTC' not in colnames:
                eval_data['dBTC'] = 0
            dBTC_idx = list(eval_data.columns).index('dBTC')
            # only sell or buy decisions, not both
            if eval_data.iloc[-1, buy_idx]*eval_data.iloc[-1, sell_idx] != 1:
                if (eval_data.iloc[-1, buy_idx] == 1 and
                    eval_data.iloc[-1, USD_idx] > strategy_dict['minfunds_USD']):
                    # do buy
                    price = eval_data.iloc[-1, hi_idx]
                    price = get_orderbook_now(exchange, 'BTC/USD')['bid_closest_price']
                    # add taker fee
                    price = price * (1+taker_fee)
                    if not np.isnan(price):
                        if (price*strategy_dict['amount_buy'] >
                            eval_data.iloc[-1, USD_idx]):
                            amount_buy_now = eval_data.iloc[-1, USD_idx] / price
                        else:
                            amount_buy_now = strategy_dict['amount_buy']
                        print('buying', amount_buy_now, 'BTC for', price, 'USD')
                        eval_data.iloc[-1, dUSD_idx] -= price*amount_buy_now
                        eval_data.iloc[-1, dBTC_idx] += amount_buy_now
                if (eval_data.iloc[-1, sell_idx] == 1 and
                    eval_data.iloc[-1, BTC_idx] > strategy_dict['minfunds_BTC']):
                    # do sell
                    price = eval_data.iloc[-1, lo_idx]
                    price = get_orderbook_now(exchange, 'BTC/USD')['ask_closest_price']
                    if not np.isnan(price):
                        if strategy_dict['amount_sell'] > eval_data.iloc[-1, BTC_idx]:
                            amount_sell_now = eval_data.iloc[-1, BTC_idx]
                        else:
                            amount_sell_now = strategy_dict['amount_sell']
                        print('selling', amount_sell_now, 'BTC for ', price, 'USD')
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
                    eval_data.iloc[-1, USD_idx] > strategy_dict['minfunds_USD']):
                    print('real trading not implemented yet')
                if (eval_data.iloc[-1, sell_idx] == 1 and
                    eval_data.iloc[-1, BTC_idx] > strategy_dict['minfunds_BTC']):
                    # do sell
                    print('real trading not implemented yet')

        # concatenate data (with all new columns)
        all_data = all_data.iloc[:-2, :]
        all_data = all_data.append(eval_data.iloc[-2:, :].copy(),
                                   ignore_index=True)

        # save
        all_data.to_excel(filename + '_' +
                          datetime.now().strftime('%Y-%U') +
                          '.xlsx')

        # wait and go for next loop
        i += 1
        time.sleep(10)  # every half interval
