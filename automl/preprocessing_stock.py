# -*- coding: utf-8 -*-
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
            params: (DataFrame) @data, e.g. stock closing price
                    (list)(int) @days, e.g. [3, 10, 20] >>> MA3, MA10, MA20
                    (str) @return_type, e.g. 'dict' >>> return dict result, 'list' >>> return list result
            return: (list/dict)(DataFrame) list of MA
        '''
        mas = {} if return_type == 'dict' else []

        for day in days:
            if return_type == 'dict':
                mas[day] = self.calculate_ma(data=data, day=day) # return dict
            else:
                mas.append(self.calculate_ma(data=data, day=day)) # return list

        return mas

    def find_crossing_point(self, A: 'List[int]', B: 'List[int]') -> 'List[int]':
        ''' find the two MA crossing point
        '''
        index = []
        for i in range(1, len(A)-1):
            if (A[i-1]>B[i-1] and A[i]<B[i]) or (A[i-1]<B[i-1] and A[i]>B[i]):
                index.append(i)
        return index

def test(stock_id=''):
    logger.info('-'*100)
    logger.info(f'*** {stock_id} ***')
    logger.info(f'start getting (stock_id={stock_id}) ...')

    stock_processor = Stock_Preprocessing()

    data = stock_processor.load_data([stock_id])
    stock_processor.save_dataframe_to_file(data=data, file_path=f'data/{stock_id}.csv')

    logger.info('... testing done.')

if __name__ == '__main__':

    test(stock_id='TSLA')
    test(stock_id='NVDA')
