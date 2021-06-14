import math
import statistics

import numpy as np
import pandas as pd
import requests
from scipy.stats import percentileofscore

from secrets import IEX_CLOUD_API_TOKEN
from stockFinder import helpers


class TickerSelectorGenerator:
    def __init__(self, analysis, amount):
        if amount == 0:
            self.amount_to_invest = amount
        else:
            self.amount_to_invest = 1000
        self.robustValue_columns = [
            'Ticker',
            'Price',
            'Number of Shares to Buy',
            'Price-to-Earnings Ratio',
            'PE Percentile',
            'Price-to-Book Ratio',
            'PB Percentile',
            'Price-to-Sales Ratio',
            'PS Percentile',
            'EV/EBITDA',
            'EV/EBITDA Percentile',
            'EV/GP',
            'EV/GP Percentile',
            'RV Score'
        ]
        self.symbol_groups = list()
        self.symbol_strings = []
        self.analysis_type = analysis
        self.analysis_list = {
            'robust': self.robustValue_columns
            # Add other analysis type
        }
        self.get_analysis_type(analysis)

    def get_analysis_type(self, analysis_type):
        # Get the function from switcher dictionary
        func = self.analysis_list.get(analysis_type, "nothing")
        self.dataframe = pd.DataFrame(columns=func)

    def create_stockList(self):
        stocks = pd.read_csv('SP500-stocks.csv')
        # Split list of stocks to ease batch API calls
        self.symbol_groups = list(helpers.chunks(stocks['Ticker'], 100))
        self.symbol_strings = []
        for i in range(0, len(self.symbol_groups)):
            self.symbol_strings.append(','.join(self.symbol_groups[i]))

    # Build RV DataFrame
    def buildRVDataFrame(self):
        self.create_stockList()
        for symbol_string in self.symbol_strings:
            batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
            data = requests.get(batch_api_call_url).json()
            for symbol in symbol_string.split(','):
                enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
                ebitda = data[symbol]['advanced-stats']['EBITDA']
                gross_profit = data[symbol]['advanced-stats']['grossProfit']
                try:
                    ev_to_ebitda = enterprise_value / ebitda
                except TypeError:
                    ev_to_ebitda = np.NaN
                try:
                    ev_to_gross_profit = enterprise_value / gross_profit
                except TypeError:
                    ev_to_gross_profit = np.NaN

                self.dataframe = self.dataframe.append(
                    pd.Series([
                        symbol,
                        data[symbol]['quote']['latestPrice'],
                        'N/A',
                        data[symbol]['quote']['peRatio'],
                        'N/A',
                        data[symbol]['advanced-stats']['priceToBook'],
                        'N/A',
                        data[symbol]['advanced-stats']['priceToSales'],
                        'N/A',
                        ev_to_ebitda,
                        'N/A',
                        ev_to_gross_profit,
                        'N/A',
                        'N/A',
                    ],
                        index=self.robustValue_columns),
                    ignore_index=True
                )
                if self.clean_dataframe():
                    self.calc_robustValue_percentiles()
                    self.calc_number_of_shares()
                else:
                    print('error in dataframe creation at ', symbol)
                    return False
        if not self.dataframe_is_empty():
            helpers.df_to_csv(self.dataframe)  # Create CSV file
            return True

    def clean_dataframe(self):
        # Clean dataframe for missing data
        # df[df.isnull().any(axis=1)].to_string()  # show all the missing data
        if self.analysis_type == 'robust':
            for column in ['Price-to-Earnings Ratio', 'Price-to-Book Ratio', 'Price-to-Sales Ratio',
                           'EV/EBITDA', 'EV/GP']:
                self.dataframe[column].fillna(self.dataframe[column].mean(), inplace=True)
        # check for the missing data
        # if self.dataframe[self.dataframe.isnull().any(axis=1)].to_string() == ' ':
        if self.dataframe.isnull().sum().sum() == 0:
            return True
        else:
            return False

    def calc_robustValue_percentiles(self):
        # Calculate Value Percentiles
        metrics = {
            'Price-to-Earnings Ratio': 'PE Percentile',
            'Price-to-Book Ratio': 'PB Percentile',
            'Price-to-Sales Ratio': 'PS Percentile',
            'EV/EBITDA': 'EV/EBITDA Percentile',
            'EV/GP': 'EV/GP Percentile'
        }
        for metric in metrics.keys():
            for row in self.dataframe.index:
                self.dataframe.loc[row, metrics[metric]] = percentileofscore(self.dataframe[metric],
                                                                             self.dataframe.loc[row, metric]) / 100
    # print(rv_dataframe[rv_dataframe.isnull().any(axis=1)].to_string()) # show all the missing data (should have
    # none now) print(rv_dataframe.to_string()) Calculate the Robust Percentile
        for row in self.dataframe.index:
            value_percentiles = []
            for metric in metrics.keys():
                value_percentiles.append(self.dataframe.loc[row, metrics[metric]])
            self.dataframe.loc[row, 'RV Score'] = statistics.mean(value_percentiles)

    # Sorting the Best 5 Value stocks in the SP500 based on their RV Score
        self.dataframe.sort_values('RV Score', ascending=True, inplace=True)
        self.dataframe = self.dataframe[:4]
        self.dataframe.reset_index(drop=True, inplace=True)

    def calc_number_of_shares(self):
        # Calculate the Number of Shares to Buy
        position_size = float(self.amount_to_invest) / len(self.dataframe.index)
        for row in self.dataframe.index:
            self.dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_size
                                                                            / self.dataframe.loc[row, 'Price'])

    def dataframe_is_empty(self):
        if self.dataframe.isnull().sum().sum() == 0:
            return False
        else:
            return True
