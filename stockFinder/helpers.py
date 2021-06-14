from datetime import date

import pandas as pd


def chunks(inputlists, n):
    n = max(1, n)
    return (inputlists[inputlist:inputlist + n] for inputlist in range(0, len(inputlists), n))


def getSP500stocks_csv(html_link):
    # Search SP500 stock
    table = pd.read_html(html_link)
    df = table[0]
    df.rename({'Symbol': 'Ticker'}, axis='columns', inplace=True)  # change column name from Symbol to Ticker
    df.to_csv('SP500_csv/SP500-Info.csv')
    df.to_csv('SP500_csv/SP500-stocks.csv', columns=['Ticker'], index=False)
    print('CSV file created')


def df_to_csv(df):
    df.to_csv('Companies/{0}{1}.csv'.format('Companies_to_buy_', str(date.today())))
