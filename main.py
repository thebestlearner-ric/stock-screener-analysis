# Description: Build a trading bot to select 3 stocks to buy and when to buy/sell them
import os
from datetime import date, timedelta

from backTester import backtest
from stockFinder import helpers as sf_helper, TickerSelector

# Ensure to install all the packages on your environment
# Ensure pip is updated
# pip install --upgrade pip
# For MacOS ensure your certificate is update to access website via SSL
# cd "/Applications/Python 3.6/" sudo "./Install Certificates.command"


AMOUNT_TO_INVEST = 10000
# Create S&P500 CSV
# Create TickerSelector object using the RobustValue analysis
MODE = 0


def run():
    sf_helper.getSP500stocks_csv('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    if os.path.exists('{0}{1}.csv'.format('Companies/COMPANIES_TO_BUY_', str(date.today()))):
        print("Good Value csv file exist")

        # strategy.init()
        end_date = date.today()
        start_date = end_date - timedelta(365)
        if MODE == 0:
            print('Run Default Strategy')
            backtest.backTest_testStrategy(AMOUNT_TO_INVEST, start_date)
        else:
            print('Run Golden Cross Strategy')
            backtest.backTest_GoldenCross(AMOUNT_TO_INVEST, start_date)
    else:
        ticker_selector = TickerSelector.TickerSelectorGenerator('robust', AMOUNT_TO_INVEST)
        if ticker_selector.buildRVDataFrame():
            print('RV CSV created')
        else:
            print('Error in RV CSV creation')


if __name__ == '__main__':
    run()
