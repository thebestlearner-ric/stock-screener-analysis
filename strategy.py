from datetime import date, timedelta

import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

from secrets import ALPHA_VANTAGE_API_KEY

# Strategy: Breakout
# Concept: Buy in case of Breakout, have a trailing Stoploss
# Buy when the current price is higher than previous high and have a trailingStoploss adjusted to follwo
# Sell when the price drops below a certain tolerance
# Dynamic approach to backtest: Volatility adjusted lookback length

# TODO
# 1) Construct structure to hold data
# 2) Learn alphavantage the daily price (current, high, close)
# 3) Learn to construct buy and sell order and have a method to do so
# 4) Backtest: create a script to call the length of data to collect /
# run the algo on the dataset

THIRTY_DAY_VOLATILITY_LENGTH = 30
initial_stop_risk = 0.98
trailing_stop_risk = 0.9
lookback_length = 20  # days
lookback_ceiling = 30
lookback_floor = 10
highest_price = 0
set_end_date = date.today()
set_start_date = set_end_date - timedelta(365 * 5)
# Build our DataFrame
stocks = pd.DataFrame()
order_book_dataframe = pd.DataFrame()
order_book_columns = []


def init():
    global stocks, order_book_dataframe, order_book_columns
    stocks = pd.read_csv('Companies/{0}{1}.csv'.format('Companies_to_buy_', str(date.today())))
    order_book_columns = [
        'Ticker',
        'Price',
        'Action',
        'Number of Shares',
        'Date'
    ]
    order_book_dataframe = pd.DataFrame(columns=order_book_columns)


def populate_stock_list(column):
    global stocks
    symbol_string = list(stocks[column])
    return symbol_string


def fill_dataframe(string, timeseries, column):
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
        ticker_dataframe = ticker_dataframe.loc[set_start_date:]
        return ticker_dataframe


def calc_intraday_volatility(data):
    global lookback_length
    today_close = data.head(THIRTY_DAY_VOLATILITY_LENGTH)
    yesterday_close = data.head(THIRTY_DAY_VOLATILITY_LENGTH + 1).iloc[1:]
    today_vol = np.std(today_close)
    yesterday_vol = np.std(yesterday_close)
    delta_vol = (today_vol - yesterday_vol) / today_vol
    lookback_length = round(lookback_length * (1 + delta_vol[0]))
    return lookback_length


def check_lookback_length(length):
    global lookback_length
    if length > lookback_ceiling:
        lookback_length = lookback_ceiling
    elif lookback_length < lookback_floor:
        lookback_length = lookback_floor
    else:
        lookback_length = length


def breakout_strategy():
    global initial_stop_risk
    global trailing_stop_risk
    global lookback_length
    global lookback_ceiling
    global lookback_floor
    global highest_price
    # global set_end_date
    # global set_start_date
    alphavantage_timeseries = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
    for symbol in populate_stock_list('Ticker')[:1]:
        # symbol_data = fill_dataframe(symbol, alphavantage_timeseries, 'Close')
        symbol_data = pd.read_csv('symbol data close.csv')
        lookback_length = calc_intraday_volatility(symbol_data)
        check_lookback_length(lookback_length)  # Dynamic lookback_length calculated
        # List of daily high
        # symbol_highs = fill_dataframe(symbol, alphavantage_timeseries, 'High')
        symbol_highs = pd.read_csv('symbol data high.csv')
        del symbol_data['date']
        del symbol_highs['date']
        symbol_highs = symbol_highs.iloc[1:]  # remove today's high
        symbol_close = np.array(symbol_data)
        last_close = np.float64(symbol_close[0])
        historical_highest_price = np.max(np.array(symbol_highs.head(lookback_length)))
        # Buy in case of breakout
        # get the last closing price and the highest high price excluding yesterday
        if (not get_is_invested(symbol)) and (last_close >= historical_highest_price):
            send_buy_order(symbol, get_numbers_of_shares(symbol), last_close)
            breakout_level = historical_highest_price
            highest_price = breakout_level
            # Create trailing stop loss once invested
            # if no order exists, send stop loss
        if not get_is_invested(symbol):
            if not check_open_order(symbol):
                set_trailing_stoploss(symbol, get_numbers_of_shares(symbol),
                                      check_stop_price(last_close, historical_highest_price, breakout_level))


def check_stop_price(closing_price, historical_high, breakout):
    # Check if the asset's price is higher than highestPrice
    # & trailing stop price not below initial stop price
    global initial_stop_risk, trailing_stop_risk, highest_price
    if closing_price > historical_high and (initial_stop_risk * breakout) < (closing_price * trailing_stop_risk):
        # Save the new high to highestPrice
        highest_price = closing_price
        # Update the stop price
        stop_price = closing_price * trailing_stop_risk
        return stop_price
    else:
        stop_price = initial_stop_risk * breakout
        return stop_price


def send_buy_order(tick, quantity, price):
    # Record buy price and quantity
    global order_book_dataframe
    order_book_dataframe = order_book_dataframe.append(
        pd.Series([
            tick,
            price,
            'Bought',
            quantity,
            date
        ],
            index=order_book_columns),
        ignore_index=True
    )
    # Return to plot


# set trailing stoploss (number of shares, stoploss price, initialStopRisk * breakoutlvl)
# change stoploss when new high are reached.
# set new high to new high
# stop price = latest close price * trailingStopRisk
def set_trailing_stoploss(tick, quantity, price):
    send_stop_order(tick, quantity, price)
    return


def send_stop_order(tick, quantity, price):
    # Record buy price and quantity
    global order_book_dataframe
    order_book_dataframe = order_book_dataframe.append(
        pd.Series([
            tick,
            price,
            'Sold',
            quantity,
            date
        ],
            index=order_book_columns),
        ignore_index=True)
    # Return to plot


def check_open_order(tick):
    # Not implemented yet
    return True


def get_is_invested(tick):
    # Check number of Bought against length number of Sold
    # if number of Bought greater than Sold = a position
    global order_book_dataframe
    is_invested_dataframe = pd.DataFrame(order_book_dataframe, columns=['Ticker', 'Action'])
    if not is_invested_dataframe.empty:
        is_invested_dataframe.set_index('Ticker', inplace=True)
        is_invested = is_invested_dataframe.loc[tick]
        number_of_actions = is_invested['Action'].value_counts()  # Count total number of actions
        number_of_bought = number_of_actions[0]
        number_of_sold = number_of_actions[1]
        if number_of_bought > number_of_sold:
            return True
        elif number_of_bought == number_of_sold:
            return False
        else:
            return False


def get_numbers_of_shares(tick):
    global stocks
    shares_dataframe = pd.DataFrame(stocks, columns=[
        'Ticker',
        'Number of Shares to Buy'
    ])
    shares_dataframe.set_index('Ticker', inplace=True)
    numbers_of_shares = shares_dataframe.loc[tick, 'Number of Shares to Buy']
    return numbers_of_shares


def clear_order_book():
    global order_book_dataframe
    order_book_dataframe.drop(order_book_dataframe.index, inplace=True)
    print("order book cleared")
