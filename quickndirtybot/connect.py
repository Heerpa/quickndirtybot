import time
from datetime import datetime
import numpy as np
import pandas as pd
import ccxt
from quickndirtybot.io import save_csv, load_csv


def connect(exchange_str='gdax'):
    return getattr(ccxt, exchange_str)()


def get_ohlcv(exchange, interval='1m', symbol='BTC/USD'):
    if exchange.has['fetchOHLCV']:
        gdaxohlcv = exchange.fetch_ohlcv(symbol, interval)
        return np.array(gdaxohlcv)


def concat(old_data, add_data):
    """input: 2d ndarray or pandas dataframe
    newest first
    """
    if not isinstance(old_data, pd.DataFrame):
        if old_data.size == 0:
            return add_data
        if add_data.size == 0:
            return old_data
        overlap = np.argwhere(old_data[:, 0] == add_data[-1, 0])
        if overlap.size == 0:
            overlap = 0
        else:
            overlap = overlap[0][0]
        old_data = old_data[overlap+1:, :]
        new_data = np.vstack((add_data, old_data))
    else:
        if len(old_data.index) == 0:
            return add_data
        if len(add_data.index) == 0:
            return old_data
        timeidx = list(add_data.columns).index('time')
        realolddata_idx = old_data.loc[:, 'time'] < add_data.iloc[0, timeidx]
        old_overwrite = old_data.loc[np.logical_not(realolddata_idx.values), :]
        # old_overwrite = old_data.loc[old_data['time'] >= add_data.iloc[0, timeidx], :]
        if len(old_overwrite.index) > len(add_data.index):
            print('new data is shorter, so I can just keep the old one')
            return old_data
        old_data = old_data.loc[realolddata_idx, :]
        new_data = old_data.append(add_data, ignore_index=True)

        # some evaluation columns would be overwritten by nans of new data
        # copy only these columns from the old data
        add_data_cols = list(add_data.columns)
        new_data_cols = list(new_data.columns)
        eval_cols = [col for col in new_data_cols if col not in add_data_cols]
        try:
            new_data.loc[old_overwrite.index, tuple(eval_cols)] = old_overwrite.loc[:, tuple(eval_cols)]
        except Exception as e:
            print('new_data index')
            print(new_data.index)
            print('old overwrite index')
            print(old_overwrite.index)
            print('Error: ', e)
    return new_data


def download_ohlcv(exchange, interval='1m', symbol='BTC/USD',
                   filename='gdax_data'):
    all_data = np.array([[]])
    try:
        all_data = load_csv(filename+'_' +
                            datetime.now().strftime('%Y-%U') +
                            '.csv')
    except:
        pass
    i = 0
    currweek = ''
    while True:
        if currweek != datetime.now().strftime('%U'):
            # empty dataset after a week
            all_data = np.array([[]])
            currweek = datetime.now().strftime('%U')
        try:
            recent_data = get_ohlcv(exchange, interval, symbol)
            all_data = concat(all_data, recent_data)
            save_csv(all_data,
                     filename+'_'+datetime.now().strftime('%Y-%U')+'.csv')
        except Exception as e:
            print('timeout, going on')
            print(e)
        # print('loop {:d}:'.format(i), 'time:', datetime.now())
        # print(filename+':', len(all_data), 'entries')
        i += 1
        time.sleep(30 * 60)  # every half an hour


def get_orderbook_now(exchange, symbol):
    '''get order book and make statistics on it
    '''
    ob = exchange.fetch_order_book(symbol)
#     print(ob)
    ob_asks = np.array(ob['asks'])
    ob_bids = np.array(ob['bids'])
    ob_stats = {}
    ob_stats['time'] = datetime.now().timestamp()
    ob_stats['ask_vol'] = np.sum(ob_asks[:, 1])
    ob_stats['ask_stdovermean_price'] = np.std(ob_asks[:, 0])/np.mean(ob_asks[:, 0])
    ob_stats['ask_spread_price'] = ob_asks[-1, 0] - ob_asks[0, 0]
    ob_stats['ask_closest_price'] = ob_asks[0, 0]
    ob_stats['ask_closest_vol'] = ob_asks[0, 1]
    ob_stats['ask_weighted_mean_price'] = np.sum((ob_asks[:, 0] * ob_asks[:, 1])/np.sum(ob_asks[:, 1]))
    ob_stats['ask_closestpromille_vol'] = np.sum(ob_asks[np.argwhere(ob_asks[:, 0]>.999*ob_asks[0, 0]), 1])
    ob_stats['bid_vol'] = np.sum(ob_bids[:, 1])
    ob_stats['bid_stdovermean_price'] = np.std(ob_bids[:, 0])/np.mean(ob_bids[:, 0])
    ob_stats['bid_spread_price'] = ob_bids[-1, 0] - ob_bids[0, 0]
    ob_stats['bid_closest_price'] = ob_bids[0, 0]
    ob_stats['bid_closest_vol'] = ob_bids[0, 1]
    ob_stats['bid_weighted_mean_price'] = np.sum((ob_bids[:, 0] * ob_bids[:, 1])/np.sum(ob_bids[:, 1]))
    ob_stats['bid_closestpromille_vol'] = np.sum(ob_bids[np.argwhere(ob_bids[:, 0]>.999*ob_bids[0, 0]), 1])
    return ob_stats


def download_orderbook(exchange, symbol='BTC/USD', interval=5):
    ob_gdax = pd.DataFrame()
    i = 0
    currweek = ''
    while True:
        if currweek != datetime.now().strftime('%U'):
            # empty dataset after a week
            ob_gdax = pd.DataFrame()
            currweek = datetime.now().strftime('%U')
        try:
            ob_dict = get_orderbook_now(exchange, symbol)
            ob_gdax = ob_gdax.append(ob_dict, ignore_index=True)
            ob_gdax.to_excel('gdax_orderbook_' +
                             datetime.now().strftime('%Y-%U') +
                             '.xlsx')
        except Exception as e:
            print('timeout, going on')
            print(e)
        print('loop {:d}:'.format(i), 'time:', datetime.now())
        print('gdax:', len(ob_gdax), 'entries')
        i += 1
        time.sleep(interval)  # in seconds


def check_credentials(exchange, credentials):
    exchange.apiKey = credentials['key']
    exchange.secret = credentials['secret']
    if 'password' in credentials.keys():
        exchange.password = credentials['password']


def get_funds(exchange, symbols=['USD', 'BTC']):
    balance = exchange.fetch_balance()
    # funds = {}
    # for symbol in symbols:
    #     funds[symbol] = balance[symbol]['total']
    return {symbol: balance[symbol]['total'] for symbol in symbols}


def trade_market_buy(exchange, symbol, amount):
    """ buy amount BTC and give away USD
    """
    exchange.create_market_buy_order(symbol, amount)


def trade_market_sell(exchange, symbol, amount):
    """ sell amount BTC and get USD
    """
    exchange.create_market_sell_order(symbol, amount)
