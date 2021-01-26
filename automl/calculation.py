import numpy as np
import pandas as pd
import traceback
from loguru import logger

class CalcIntersection():

    def calculate_ma(self, data=pd.DataFrame, day=3):
        ''' calculate Moving Average (MA)
            params: (DataFrame) @data, e.g. stock closing price
                    (int) @day Size of the moving window, e.g. 3 >>> MA3
            return: (DataFrame) MA
        '''
        ma = pd.DataFrame.rolling(data, window=day).mean()
        return ma

    # def calculate_intersection(self, data=pd.DataFrame,as_of_date=None)->'float':
    def calculate_intersection(self, data=pd.DataFrame, window1=3, window2=10, as_of_date=None)->'float':
        ''' calculate the Closing price when ma3 = ma10
            今天是什麼收市價，ma3 & ma10 才會再次交差 (e.g. ma3=200, ma10=190, closing需要 XXX)
            params: (DataFrame) @data
                    (int) @window1: size of moving window of first MA, e.g. 3
                    (int) @window2: size of moving window of second MA, e.g. 10
                    (string) @as_of_date, e.g. df['Date']<='2020-05-03'
                    * 如「已收市」時run, data應截至收市日, 預測「明天」「收巿價」
                    * 如「開巿中」時run, data應截至「前一日」, 預測「今天」「收巿價」
            return: (float) the value when ma3 intersect ma5
        '''
        logger.debug(f'data.shape:{data.shape}')
        if not isinstance(data.index, pd.RangeIndex): # check if DataFrame index is RangeIndex (e.g. read from csv. 0, 1, 2 ...)
        # if isinstance(data.index, pd.DatetimeIndex): # check if DataFrame index is DatetimeIndex (e.g. download from yfinance)
        # if isinstance(data.index, pd.Index): # check if DataFrame index is normal named index (e.g. read from csv, specific index_col='xx')
            logger.debug(f'type(data.index):{type(data.index)}, RangeIndex not found, convert to RangeIndex')
            data = data.reset_index()

        if as_of_date is not None:
            # logger.debug(data.index[data['Date']==date].tolist()) # TBD
            # end_date = data.index[data['Date']==date].tolist()[0] # TBD
            # data = data[:end_date] # TBD
            data = data[data['Date']<=as_of_date]
            print(data.tail())
        logger.debug(f'after: data.shape:{data.shape}')
        close = data['Close']
        sum1 = pd.DataFrame.rolling(close, window= (window1-1)).sum().iat[-1]
        sum2 = pd.DataFrame.rolling(close, window= (window2-1)).sum().iat[-1]
        intersection = (window1*sum2 - window2*sum1)/float(window2-window1)
        # e.g. intersection = (3*sum2 - 10*sum1)/float(10-7)
        return intersection

    def calculate_difference(self, data=pd.DataFrame, window1=3, window2=10, date=None)->'float':
    # def calculate_difference(self, data=pd.DataFrame,date=None)->'float':
        ''' calculate difference needed to reach intersect point
            params: (DataFrame) @data
                    (int) @window1: size of moving window of first MA
                    (int) @window2: size of moving window of second MA
                    (string) @date
            return: (float) value of difference
        '''
        cross_point = self.calculate_intersection(data,window1,window2,date)
        if date is not None:
            end_date = data.index[data['Date']==date].tolist()[0]
            data = data[:end_date]
        yesterday_close = data['Close'].iat[-1]
        difference = cross_point - yesterday_close
        difference_percent = cross_point / yesterday_close -1
        return difference, difference_percent

    def cross_signal(self, data=pd.DataFrame, window1=3, window2=10)->'int':
        ''' check if first MA and second MA crossed in last 2 days
            params: (DataFrame) @data
                (int) @window1: size of moving window of first MA
                (int) @window2: size of moving window of second MA
            return: (int) 1 if crossed, 0 otherwise.
        '''
        first_entries = max(window1,window2)*2
        close = data['Close'][-first_entries:]
        ma_df = pd.concat([self.calculate_ma(close, window1),self.calculate_ma(close, window2)], axis=1)
        # logger.debug(ma_df.tail())
        ma_1, ma_2 = ma_df.iloc[-1,0], ma_df.iloc[-1,1]
        day1 = int(ma_1/ma_2)
        ma_1, ma_2 = ma_df.iloc[-2,0], ma_df.iloc[-2,1]
        day2 = int(ma_1/ma_2)
        if day1 == day2:
            return 0
        else:
            return 1

    def calculate_mas_crossing(self, days:'list[int]', data=pd.DataFrame)->'pd.DataFrame':
        ''' calculate mas crossing signal, e.g. ma3 x ma5, ma3 x ma10 ...
            params: (list) @days, e.g. days = [3, 5, 10]
            return: (pd.DataFrame) mas crossing signals, e.g. ['3x5']=1, ['3x10']=0 ...
        '''
        crossing_mas = {} # e.g. crossing_mas[3x5], crossing_mas[3x10] ...
        for day in days:
            for cross_day in days:
                if day != cross_day and f'{cross_day}x{day}' not in crossing_mas:
                    crossing_mas[f'{day}x{cross_day}'] = self.cross_signal(data, day, cross_day)
        return crossing_mas

    def trade(self, action='buy', price=0.0, amount=0.0, volume=0, last_trade_price=0)->'float,float':
        ''' start a trade (buy/sell),
            @param: (string) action, 'buy'/'sell'
                    (float) amount, for 'buy'&'sell'
                    (float) price, for 'buy'&'sell'
                    (int) volume, for sell only
            e.g.
            <buy> : (string) action, (float) amount, (float) price
            <sell>: (string) action
            return amount, volume, price_different_percent
        '''
        price_different_percent = round((price - last_trade_price)/last_trade_price, 3) if last_trade_price!=0 else 0.0
        if action == 'buy':
            volume = amount // price
            amount -= (volume * price)
            logger.debug(f'{action}: {volume} at ${price} ([+-]{round(price_different_percent*100,2)}%) (remain: amount={amount}, volume={volume})')
            trade_price = price
        elif action == 'sell':
            amount += volume * price
            logger.debug(f'{action}: {volume} at ${price} ({round(price_different_percent*100,2)}%) (remain: amount:{amount}, volume:0)')
            volume = 0
            trade_price = price

        return amount, volume, trade_price, price_different_percent

    def calculate_profit(self, data:'pd.DataFrame', init_capital:'float')->'float':
        ''' calculate the profit base on signal (data['signal'])
            return (float) gain, (float) gain_percent, e.g. 10234, 0.45

            * data MUST HAVE 'signal' field, e.g. data['signal']
        '''
        logger.debug(f'calculate_profit(init_capital={init_capital}) ...')
        amount = init_capital; volume = 0
        gain_percent = 0.0 # 0.1 >>> gain 10%, -0.23 >>> loss 23%
        trade_price = 0

        for i in range(len(data)):
            signal = data.iloc[i]['signal'] # 'buy'/'sell'
            price = data.iloc[i]['Close']
            if signal != '-':
                logger.debug(f"{data.iloc[i]['Date']} - {signal}")
                amount, volume, trade_price, price_different_percent = self.trade(action=signal, price=price, amount=amount, volume=volume, last_trade_price=trade_price)
            # if data.iloc[i]['signal'] == 'buy':
                # self.trade(action='buy', price=price, amount=amount, volume=volume)

        # sell the remaining volume to finalize the profit
        if volume:
            amount, volume, trade_price, price_different_percent = self.trade(action='sell', price=price, amount=amount, volume=volume, last_trade_price=trade_price)

        gain = amount - init_capital
        gain_percent = round(amount/init_capital-1, 2)
        return gain, gain_percent


def test(stock_id=''):

    logger.info('-'*100)
    logger.info(f'*** {stock_id} ***')
    logger.info(f'start calculating (stock_id={stock_id}) ...')
    # stock_id = 'stocks'

    df = pd.read_csv(f"./data/{stock_id}.csv")
    print(df.tail())
    calc = CalcIntersection()

    window1 = 3
    window2 = 13

    print('-'*50)
    print('Cross point:',calc.calculate_intersection(df, window1=window1, window2=window2))
    # print('Cross point:',calc.calculate_intersection(df,'2020-05-05'))

    print('-'*50)
    print('next day, Differnce:',calc.calculate_difference(df, window1=window1, window2=window2))
    # print('Differnce:',calc.calculate_difference(df))

    print('-'*50)
    print('today, Cross signal:\n',calc.cross_signal(df,window1=window1, window2=window2))

    print('='*50)
    print('today (to become cross), Differnce:',calc.calculate_difference(df[:-1], window1=window1, window2=window2))
    # print('Differnce:',calc.calculate_difference(df))

    print('='*50)
    print('last day, Cross signal:\n',calc.cross_signal(df[:-1],window1=window1, window2=window2))

    print('-'*60)
    # days = [3, 5, 10]
    days = range(1, 14)
    mas_crossings = calc.calculate_mas_crossing(days=days, data=df)
    print('mas_crossings:', mas_crossings)

def backtest(stock_id:'string', start_date='2020-01-01', init_capital=10000):
    logger.info('-'*100)
    logger.info(f'*** {stock_id} ***')
    logger.info(f'start backtesting (stock_id={stock_id}) ...')

    # read data
    df = pd.read_csv(f"./data/{stock_id}.csv")
    print(df.tail())
    calc = CalcIntersection()

    # cut by the start_date
    df = df[df['Date'] >= start_date]
    print(df.head())

    # get signal by features
    # df = df[df['ma3x10']>]
    df['signal'] = '-'
    df.loc[df['ma3x13']>0,'signal'] = 'buy'
    df.loc[df['ma3x13']<0,'signal'] = 'sell'
    # df['signal'].fillna('-', inplace=True)
    print(df.tail(12))

    amount = init_capital
    gain, gain_percent = calc.calculate_profit(data=df, init_capital=amount)
    print(f'amount: {amount}, gain: {gain}, gain_percent: {gain_percent}')

if __name__ == '__main__':
    test(stock_id='TSLA')
    test(stock_id='NVDA')
    test(stock_id='SYNH')
    test(stock_id='^DJI')
    test(stock_id='QQQ')
    test(stock_id='TQQQ')
    test(stock_id='ARKW')
    test(stock_id='ARKG')
    test(stock_id='ARKK')
    test(stock_id='NKLA')
    # test(stock_id='MSFT')

    # backtest(stock_id='TQQQ')
    # backtest(stock_id='TSLA', start_date='2019-01-01', init_capital=10000)
    # backtest(stock_id='NVDA', start_date='2019-01-01', init_capital=10000)
    # backtest(stock_id='SYNH', start_date='2020-01-01', init_capital=10000)
    # backtest(stock_id='^DJI', start_date='2020-01-01', init_capital=1000000)
    # backtest(stock_id='QQQ', start_date='2019-01-01', init_capital=10000)
    # backtest(stock_id='TQQQ', start_date='2020-01-01', init_capital=10000)
    # backtest(stock_id='ARKW', start_date='2020-01-01', init_capital=10000)