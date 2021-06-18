import backtrader
from alpha_vantage.timeseries import TimeSeries

from secrets import ALPHA_VANTAGE_API_KEY
from strategies import goldenCross, testStrategy
from strategies import helpers as strategy_helper


def backTest_testStrategy(amount_to_invest, from_date):
    cerebro = backtrader.Cerebro()
    # Add data feed
    alphavantage_timeseries = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
    for symbol in strategy_helper.populate_stock_list('Ticker'):
        symbol_data = strategy_helper.fill_dataframe(symbol, alphavantage_timeseries, '', from_date)
        data = backtrader.feeds.PandasData(dataname=symbol_data)
        cerebro.addsizer(backtrader.sizers.FixedSize, stake=strategy_helper.get_numbers_of_shares(symbol))
        cerebro.addstrategy(testStrategy.TestStrategy)
        cerebro.adddata(data)
        cerebro.broker.setcash(amount_to_invest)
        print('============================================')
        print('Current ticker is:', symbol)
        print('Starting Portfolio Value: %.2f' % cerebro.broker.get_value())
        cerebro.run()
        print('Final Portfolio Value: %.2f' % cerebro.broker.get_value())
        print('============================================')
        cerebro.plot()


def backTest_GoldenCross(amount_to_invest, from_date):
    cerebro = backtrader.Cerebro()
    alphavantage_timeseries = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
    for symbol in strategy_helper.populate_stock_list('Ticker'):
        symbol_data = strategy_helper.fill_dataframe(symbol, alphavantage_timeseries, '', from_date)
        data = backtrader.feeds.PandasData(dataname=symbol_data)
        cerebro.addsizer(backtrader.sizers.FixedSize, stake=strategy_helper.get_numbers_of_shares(symbol))
        cerebro.addstrategy(goldenCross.GoldenCrossStrategy, symbol)
        cerebro.adddata(data)
        cerebro.broker.setcash(amount_to_invest)
        print('============================================')
        print('Current ticker is:', symbol)
        print('Starting Portfolio Value: %.2f' % cerebro.broker.get_value())
        cerebro.run()
        print('Final Portfolio Value: %.2f' % cerebro.broker.get_value())
        print('============================================')
        cerebro.plot()

