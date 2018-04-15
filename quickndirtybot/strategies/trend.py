# strategy based on trend
from util import moving_fun, diff
from scipy.signal import butter, lfilter


def sumoversumabs(x):
#     print(x)
#     print(x[1:])
#     print(x[:-1])
    diffx = (x[1:].values-x[:-1].values)/x[1:].values
#     print(diffx)
#     print(np.sum(diffx)/np.sum(np.abs(diffx)))
    return np.mean(diffx)#/np.sum(np.abs(diffx))


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def strat_trend_measure(dataframe, duration=3):
#     moving_fun(dataframe, 'highest', blanking=0, duration=duration, newname='trend_hi', fun=sumoversumabs)
#     moving_fun(dataframe, 'lowest', blanking=0, duration=duration, newname='trend_lo', fun=sumoversumabs)
#     moving_fun(dataframe, 'highest', blanking=0, duration=2*duration, newname='trend_hi*2', fun=sumoversumabs)
#     moving_fun(dataframe, 'lowest', blanking=0, duration=2*duration, newname='trend_lo*2', fun=sumoversumabs)
#     moving_fun(dataframe, 'highest', blanking=0, duration=10*duration, newname='trend_hi*10', fun=sumoversumabs)
#     moving_fun(dataframe, 'lowest', blanking=0, duration=10*duration, newname='trend_lo*10', fun=sumoversumabs)
#
#     # percent change
#     dataframe['diff-hi'] = 0
#     diffidx = list(dataframe.columns).index('diff-hi')
#     hiidx = list(dataframe.columns).index('highest')
#     idcs_all = list(dataframe.index)
#     dataframe.iloc[idcs_all[1:], diffidx] = ((dataframe.iloc[idcs_all[1:], hiidx].values -
#                                               dataframe.iloc[idcs_all[:-1], hiidx].values) /
#                                              dataframe.iloc[idcs_all[1:], hiidx].values)
#     # bandpass filters
#     dataframe['bandpass_hi_3-10'] = butter_bandpass_filter(dataframe['diff-hi'], 1/10, 1/3, 1, 1)
#     dataframe['bandpass_hi_10-30'] = butter_bandpass_filter(dataframe['diff-hi'], 1/30, 1/10, 1, 1)
    dataframe['bp_hi_3-10'] = butter_bandpass_filter(dataframe['highest']-dataframe.loc[0, 'highest'], 1/10, 1/3, 1, 1)/dataframe['highest']
    moving_fun(dataframe, 'bp_hi_3-10', 0, 3, 'sma_bp_hi_3-10')
    diff(dataframe, 'sma_bp_hi_3-10', 'dsma_bp_hi_3-10')
    dataframe['bp_hi_3-120'] = butter_bandpass_filter(dataframe['highest']-dataframe.loc[0, 'highest'], 1/120, 1/3, 1, 1)/dataframe['highest']
    moving_fun(dataframe, 'bp_hi_3-120', 0, 3, 'sma_bp_hi_3-120')
    diff(dataframe, 'sma_bp_hi_3-120', 'dsma_bp_hi_3-120')
    dataframe['bp_hi_3-2000'] = butter_bandpass_filter(dataframe['highest']-dataframe.loc[0, 'highest'], 1/2000, 1/3, 1, 1)/dataframe['highest']
    dataframe['bp_hi_10-30'] = butter_bandpass_filter(dataframe['highest']-dataframe.loc[0, 'highest'], 1/30, 1/10, 1, 1)/dataframe['highest']
    dataframe['bp_hi_30-120'] = butter_bandpass_filter(dataframe['highest']-dataframe.loc[0, 'highest'], 1/120, 1/30, 1, 1)/dataframe['highest']
    dataframe['bp_hi_500-2000'] = butter_bandpass_filter(dataframe['highest']-dataframe.loc[0, 'highest'], 1/2000, 1/500, 1, 1)/dataframe['highest']
    dataframe['bp_hi_1000-5000'] = butter_bandpass_filter(dataframe['highest']-dataframe.loc[0, 'highest'], 1/5000, 1/1000, 1, 1)/dataframe['highest']


def strat_trend_findbuy(dataframe, colname='bp_hi_3-120', threshold=.01):
    dataframe.loc[((dataframe[colname] > threshold) &
                   (dataframe['dsma_' + colname] > 0)
                  )
                  , 'buy'] = 1


def strat_trend_findsell(dataframe, colname='bp_hi_3-120', threshold=.01):
    dataframe.loc[((dataframe['dsma_' + colname] < 0)
                  )
                  , 'sell'] = 1

# print(sumoversumabs(np.array([3, -3, 2])))
