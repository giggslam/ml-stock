# -*- coding: utf-8 -*-
import traceback
import logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S: %p') # show DateTime in logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

from preprocessing import Preprocessing

class Stock_Preprocessing(Preprocessing):

    import yfinance as yf
    import pandas as pd
    agent_id = ''

    def __init__(self, agent_id='', debug=False):
        logger.info('Init class Stock_Preprocessing ...') # DEBUG
        self.agent_id = agent_id
        logger.info('... Init class Stock_Preprocessing done') # DEBUG

    def download_stock_data(self, stock_ids:'List[string]', period='max', start='', end='', group_by='ticker')->'pd.DataFrame':
        ''' download data from yahoo finance
            if params 'start' & 'end' passed, only specific date data will be downloaded

            params: (list) @stock_ids, list of stock id, e.g. stocks=['NVDA','TSLA','UGLD']
                    (string) @period, period of data to download ('max', '1y', '5y'), e.g. period='max'
                    (string) @start, download data from start of date, e.g. start='2020-04-28'
                    (string) @end, download data until end of date, e.g. end='2020-04-28'
                    (string) @group_by, set default group by ticker, then can use data['NVDA'] to access
            return: (pd.DataFrame) stock data
        '''
        try:
            logger.info(f'download_stock_data(stock_ids={stock_ids}) ...') # DEBUG
            data = None

            # data = self.yf.download(stock_ids, period=period, start=start, end=end, group_by=group_by)
            if start or end:
                data = self.yf.download(stock_ids, period=period, start=start, end=end)
            else:
                data = self.yf.download(stock_ids, period=period)

        except Exception as e:
            logger.error('download_stock_data()')
            logger.error(self.traceback.format_exc())
            logger.error(e)
        finally:
            logger.info('... download_stock_data()') # DEBUG
            return data

    def load_data(self, stock_ids=[], period='max', start='', end='')->'pd.DataFrame':
        ''' load stock data by yfinance
            TODO:
        '''
        try:
            logger.info(f'load_data(stock_ids={stock_ids}) ...') # DEBUG
            data = None

            data = self.download_stock_data(stock_ids, period=period, start=start, end=end)

        except Exception as e:
            logger.error(self.traceback.format_exc())
            logger.error(e)
        finally:
            logger.info('... load_data()') # DEBUG
            return data

    def calculate_ma(self, data=pd.DataFrame, day=3):
        ''' calculate Moving Average (MA)
            params: (DataFrame) @data, e.g. stock closing price
                    (int) @day Size of the moving window, e.g. 3 >>> MA3
            return: (DataFrame) MA
        '''
        ma = self.pd.DataFrame.rolling(data, window=day).mean()
        return ma

    def calculate_mas(self, data=pd.DataFrame, days=[], return_type='dict'):
        ''' calculate list of Moving Average (MA)
            params: (DataFrame) @data, e.g. stock closing price (data['Close'])
                    (list)(int) @days, e.g. [3, 10, 20] >>> MA3, MA10, MA20
                    (str) @return_type, e.g. 'dict' >>> return dict result, 'list' >>> return list result
            return: (list/dict)(DataFrame) list of MA
        '''
        logger.info('calculate_mas() ...')
        mas = {} if return_type == 'dict' else []

        for day in days:
            if return_type == 'dict':
                mas[day] = self.calculate_ma(data=data, day=day) # return dict
            else:
                mas.append(self.calculate_ma(data=data, day=day)) # return list

        logger.info('... calculate_mas()')
        return mas

    def find_crossing_point(self, A: 'List[int]', B: 'List[int]') -> 'List[int]':
        ''' find the two MA crossing point
            params: (list)(int) @A, e.g. MA3
                    (list)(int) @B, e.g. MA10
            return: (list)(int) index of crossing point (signal=1)
        '''
        index = []
        for i in range(1, len(A)-1):
            if (A[i-1]>B[i-1] and A[i]<B[i]) or (A[i-1]<B[i-1] and A[i]>B[i]):
                index.append(i)
        return index

    def calcaulate_mas_crossing_points(self, A: 'List[int]', B: 'List[int]') -> 'List[int]':
        ''' find the two MA crossing point
            params: (list)(int) @A, e.g. MA3
                    (list)(int) @B, e.g. MA10
            return: (list)(int) crossing point (0: two line parallel, 1: crossing signal)
        '''
        try:
            logger.info('calcaulate_mas_crossing_points() ...')
            crossing_points = [0 for i in range(len(A))] # init list w/ default value
            for i in range(1, len(A)):
                if (A[i-1]>B[i-1] and A[i]<B[i]) or (A[i-1]<B[i-1] and A[i]>B[i]):
                    crossing_points[i] = 1
                    # crossing_points.append(1)
                # else:
                    # crossing_points.append(0)
        except Exception as e:
            logger.error('ERROR: calcaulate_mas_crossing_points()')
            logger.error(self.traceback.format_exc())
            logger.error(e)
        finally:
            logger.info('... calcaulate_mas_crossing_points()')
            return crossing_points

    def calculate_batch_mas_crossing_points(self, data=pd.DataFrame, days=[])->'dict':
        ''' calculate list of MAs crossing points (e.g. MA3x10, MA3x20 ...)
            params: (DataFrame) @data, e.g. stock ma (data['MA3'], data['MA10'] ...)
                    (list)(int) @days, e.g. [3, 10, 20] >>> MA3, MA10, MA20
            return: (dict)(DataFrame) list of MAs crossing points
        '''
        logger.info('calculate_batch_mas_crossing_points() ...')
        crossing_points = {}

        for day in days:
            for cross_day in days:
                if day != cross_day and f'ma{cross_day}x{day}' not in crossing_points:
                    crossing_points[f'ma{day}x{cross_day}'] = self.calcaulate_mas_crossing_points(data[f'ma{day}'], data[f'ma{cross_day}'])
        return crossing_points

    def merge_mas_into_data(self, mas:'dict[pd.DataFrame]', data=pd.DataFrame) -> 'pd.DataFrame':
        ''' merge calculated mas (list of df, def calculate_mas) into data (df)
            params: (list)(DataFrame) @mas
            return: (DataFrame) merged stock data
        '''
        for day in mas:
            data[f'ma{day}'] = mas[day]

        return data

    def merge_dict_into_data(self, dict_of_df:'dict[pd.DataFrame]', data=pd.DataFrame) -> 'pd.DataFrame':
        ''' merge dict of df into data (df), e.g. cross_signals (cross_signals['MA3x10'] ...)
            params: (dict)(DataFrame) @dict_of_df
            return: (DataFrame) merged stock data
        '''
        for crossing_ma in dict_of_df:
            data[crossing_ma] = dict_of_df[crossing_ma]

        return data

def test(stock_id=''):
    logger.info('-'*100)
    logger.info(f'*** {stock_id} ***')
    logger.info(f'start getting (stock_id={stock_id}) ...')

    stock_processor = Stock_Preprocessing()

    data = stock_processor.load_data([stock_id])
    stock_processor.save_dataframe_to_file(data=data, file_path=f'data/{stock_id}.csv')

    logger.info('... testing done.')

def test_pipeline(stock_id=''):
    logger.info('-'*100)
    logger.info(f'*** {stock_id} ***')
    logger.info(f'start getting (stock_id={stock_id}) ...')

    stock_processor = Stock_Preprocessing()

    # load stock data from Yahoo
    data = stock_processor.load_data([stock_id])

    # ma_days = [2, 3, 5, 9, 10]
    ma_days = range(1, 11)

    # calculate mas
    mas = stock_processor.calculate_mas(data=data['Close'], days=ma_days)
    print(f'len(mas[3]):{len(mas[3])}')
    print(f'len(mas[10]):{len(mas[10])}')

    # merge mas back into stock data
    data = stock_processor.merge_mas_into_data(mas=mas, data=data)
    print(data.tail(12))

    # ma crossing signal (count for the latest price)
    # print('-'*100)
    # from calculation import CalcIntersection
    # calc = CalcIntersection()
    # cross_signals = calc.calculate_mas_crossing(days=ma_days, data=data)
    # print(cross_signals)

    # calc crossing signal (e.g. 3x10)
    # print('-'*100)
    # cross_signals = stock_processor.calcaulate_mas_crossing_points(mas[3], mas[10])
    # # print(cross_signals[:-10])
    # print(f'len(cross_signals):{len(cross_signals)}')
    # print(f'data:{len(data)}')
    # data['ma3x10'] = cross_signals

    # calc all crossing signal (e.g. 3x5, 3x10, 5x10 ...)
    print('-'*100)
    cross_signals = stock_processor.calculate_batch_mas_crossing_points(data=data, days=ma_days)

    # merge cross_signals back into stock data
    data = stock_processor.merge_dict_into_data(dict_of_df=cross_signals, data=data)
    print(data.tail(12))

    # save stock data to csv
    stock_processor.save_dataframe_to_file(data=data, file_path=f'data/{stock_id}.csv')

    logger.info('... done')

if __name__ == '__main__':

    # test load stock data & save to csv
    # test(stock_id='TSLA')
    # test(stock_id='NVDA')

    # test pipeline
    test_pipeline(stock_id='NVDA')
