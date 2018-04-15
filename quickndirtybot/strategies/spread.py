# strategy based on spread
def strat_spread_measure(dataframe):
    dataframe['spread'] = (dataframe['highest'] - dataframe['lowest'])/dataframe['highest']
    return

def strat_spread_findbuy(dataframe):
    return

def strat_spread_findsell(dataframe):
    return
