import numpy as np
from numpy import convolve
import matplotlib.pyplot as plt


def movingaverage(values, window):
    weights = np.repeat(1.0, window)/window
    sma = np.convolve(values, weights, 'valid')
    return sma


def moving_fun(dataframe, col, blanking, duration, newname='movmin', fun=min):
    """blanking: # timepoints between 'now' and evaluation. duration: # timepoints to evaluate"""
    dataframe[newname] = np.nan
    colidx = list(dataframe.columns).index(col)
    newnameidx = list(dataframe.columns).index(newname)
    datalen = len(dataframe)
    dataframe.iloc[blanking+duration:, newnameidx] = np.fromiter((fun(dataframe.iloc[idx:idx+duration, colidx])
                                                     for idx in range(datalen-blanking-duration)),
                                                     dtype=np.float64)


def percent_change(dataframe, col, newname='percent_change'):
    dataframe[newname] = 0
    newidx = list(dataframe.columns).index(newname)
    colidx = list(dataframe.columns).index(col)
    idcs_all = list(dataframe.index)
    dataframe.iloc[idcs_all[1:], newidx] = ((dataframe.iloc[idcs_all[1:], colidx].values -
                                              dataframe.iloc[idcs_all[:-1], colidx].values) /
                                             dataframe.iloc[idcs_all[1:], colidx].values)

def diff(dataframe, col, newname='percent_change'):
    dataframe[newname] = 0
    newidx = list(dataframe.columns).index(newname)
    colidx = list(dataframe.columns).index(col)
    idcs_all = list(dataframe.index)
    dataframe.iloc[idcs_all[1:], newidx] = (dataframe.iloc[idcs_all[1:], colidx].values -
                                            dataframe.iloc[idcs_all[:-1], colidx].values)
