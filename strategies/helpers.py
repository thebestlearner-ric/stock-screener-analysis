from datetime import date

import pandas as pd


def populate_stock_list(column):
    stocks = pd.read_csv('Companies/{0}{1}.csv'.format('Companies_to_buy_', str(date.today().today())))
    symbol_string = list(stocks[column])
    return symbol_string


def get_numbers_of_shares(tick):
    stocks = pd.read_csv('Companies/{0}{1}.csv'.format('Companies_to_buy_', str(date.today().today())))
    shares_dataframe = pd.DataFrame(stocks, columns=[
        'Ticker',
        'Number of Shares to Buy'
    ])
    shares_dataframe.set_index('Ticker', inplace=True)
    numbers_of_shares = shares_dataframe.loc[tick, 'Number of Shares to Buy']
    return numbers_of_shares


def fill_dataframe(string, timeseries, column, start_date):
    ts_data, meta_data = timeseries.get_daily(symbol=string, outputsize='full')
    if column == 'Close':
        my_columns = [column]
        ticker_dataframe = pd.DataFrame(columns=my_columns)
        ticker_data = ts_data['4. close']  # in pandas dataframe daily closing price
        ticker_dataframe = ticker_data.to_frame()
        ticker_dataframe.columns = my_columns
        return ticker_dataframe
    elif column == 'High':
        my_columns = [column]
        ticker_dataframe = pd.DataFrame(columns=my_columns)
        ticker_data = ts_data['2. high']
        ticker_dataframe = ticker_data.to_frame()
        ticker_dataframe.columns = my_columns
        return ticker_dataframe
    else:
        my_columns = ['High', 'Low', 'Open', 'Close', 'Volume']
        ticker_dataframe = pd.DataFrame(columns=my_columns)
        ticker_dataframe = ts_data
        ticker_dataframe.sort_index(inplace=True)
        ticker_dataframe.columns = my_columns
        ticker_dataframe = ticker_dataframe.loc[start_date:]
        return ticker_dataframe
