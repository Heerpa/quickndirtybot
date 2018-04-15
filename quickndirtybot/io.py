import numpy as np
import pandas as pd
import json
from datetime import datetime


def save_csv(array, name):
    np.savetxt(name, array, delimiter=',')


def load_csv(name):
    return np.genfromtxt(name, delimiter=',')


def split_data(array, nrpartitions=3):
    bunchsize = int(len(array)/nrpartitions)
    return [array[i*bunchsize:(i+1)*bunchsize, :]
            for i in range(nrpartitions)]


def pandize_csv(data):
    # sort
    idx = np.argsort(data[:, 0])
    data = data[idx, :]
    # fill missing time points with NaN.
    deltats = data[1:, 0] - data[:-1, 0]
    deltat = min(deltats)
    gaps = np.argwhere(deltats > deltat)
    inserted = 0
    for gap in gaps:
        gap = gap[0] + inserted
        addlines = np.arange(start=data[gap, 0]+deltat,
                             stop=data[gap+1, 0], step=deltat)
        adddata = np.ones((len(addlines), data.shape[1])) * np.nan
        adddata[:, 0] = addlines
        inserted = inserted + len(addlines)
        data = np.vstack((data[:gap+1, :], adddata, data[gap+1:, :]))
    cols = ['time', 'open', 'highest', 'lowest', 'closing', 'volume']
    df = pd.DataFrame(data=data, columns=cols)
    return df


def load_json(filename):
    data = pd.read_json(filename)
    data.rename(index=str, columns={'H': 'highest', 'L': 'lowest',
                                    'C': 'closing', 'O': 'open', 'V': 'volume',
                                    'T': 'T', 'BV': 'BV'},
                inplace=True)
    data['time'] = data['T'].map(
                lambda x: datetime.strptime(x,
                                            '%Y-%m-%dT%H:%M:%S').timestamp()*1000)
    data.reset_index(inplace=True, drop=True)
    return data


def load_config(filename='config.json'):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config


def get_balance(exchange):
    """exchange must be connected and credentials approved
    """
    return exchange.fetch_balance()
