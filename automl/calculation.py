import numpy as np
import pandas as pd
import traceback
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

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
        logger.debug(ma_df.tail())
        ma_1, ma_2 = ma_df.iloc[-1,0], ma_df.iloc[-1,1]
        day1 = int(ma_1/ma_2)
        ma_1, ma_2 = ma_df.iloc[-2,0], ma_df.iloc[-2,1]
        day2 = int(ma_1/ma_2)
        if day1 == day2:
            return 0
        else:
            return 1

def test(stock_id=''):

    logger.info('-'*100)
    logger.info(f'*** {stock_id} ***')
    logger.info(f'start calculating (stock_id={stock_id}) ...')
    # stock_id = 'stocks'

    df = pd.read_csv(f"./data/{stock_id}.csv")
    print(df.tail())
    calc = CalcIntersection()

    print('-'*50)
    print('Cross point:',calc.calculate_intersection(df))
    # print('Cross point:',calc.calculate_intersection(df,'2020-05-05'))

    print('-'*50)
    print('Differnce:',calc.calculate_difference(df))
    # print('Differnce:',calc.calculate_difference(df))

    print('-'*50)
    print('Cross signal:',calc.cross_signal(df,3,10))

if __name__ == '__main__':
    test(stock_id='TSLA')
    test(stock_id='NVDA')
