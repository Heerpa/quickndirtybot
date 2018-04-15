import numpy as np
from quickndirtybot.strategies.util import moving_fun


def measure(dataframe, smaperiod, minmaxperiod):
    """measure things on dataframe
    smaperiod
        period in minutes of moving average
    minmaxperiod
        period to calculate the minimum/maximum over, in minutes
    """
    # get deltat in min; time is in ms
    timeidx = list(dataframe.columns).index('time')
    basic_clock = int((dataframe.iloc[1, timeidx] -
                       dataframe.iloc[0, timeidx])/60000)
    tperiod_minmax = int(minmaxperiod / basic_clock)
    tperiod_smalong = int(2*smaperiod / basic_clock)
    tperiod_smashort = int(smaperiod / basic_clock)

    # moving averages of hi and lo prices
    moving_fun(dataframe, 'highest', blanking=0, duration=tperiod_smashort,
               newname='sma-hi-now', fun=np.mean)
    moving_fun(dataframe, 'lowest', blanking=0, duration=tperiod_smashort,
               newname='sma-lo-now', fun=np.mean)
    # moving average of one period previously
    moving_fun(dataframe, 'highest', blanking=tperiod_smashort,
               duration=tperiod_smashort,
               newname='sma-hi-prev', fun=np.mean)
    moving_fun(dataframe, 'lowest', blanking=tperiod_smashort,
               duration=tperiod_smashort,
               newname='sma-lo-prev', fun=np.mean)

    # moving min and max of hi nd lo prices
    moving_fun(dataframe, 'sma-hi-now', blanking=2*tperiod_smashort,
               duration=tperiod_minmax,
               newname='min-hi-prev', fun=np.min)
    moving_fun(dataframe, 'sma-lo-now', blanking=2*tperiod_smashort,
               duration=tperiod_minmax,
               newname='max-lo-prev', fun=np.max)
#     moving_fun(dataframe, 'highest', blanking=tperiod_smashort, duration=tperiod_minmax,
#                newname='min-hi', fun=np.min)
#     moving_fun(dataframe, 'lowest', blanking=tperiod_smashort, duration=tperiod_minmax,
#                newname='max-lo', fun=np.max)
    # quotient of max and min
    dataframe['max/min'] = dataframe['max-lo-prev']/dataframe['min-hi-prev']


def findbuy(dataframe, thresh_maxovermin=1.0075):
    """find time points for buying"""
    dataframe.loc[((dataframe['sma-hi-now'] > dataframe['sma-hi-prev']) &
                   (dataframe['sma-hi-prev'] < dataframe['min-hi-prev']) &
                   (dataframe['max/min'] > thresh_maxovermin)
                  ),
                  'buy'] = 1


def findsell(dataframe, thresh_maxovermin=1.0075):
    """find time points for selling"""
    dataframe.loc[((dataframe['sma-lo-now'] < dataframe['sma-lo-prev']) &
                   (dataframe['sma-lo-prev'] > dataframe['max-lo-prev']) &
                   (dataframe['max/min'] > thresh_maxovermin)
                  )
                  , 'sell'] = 1
