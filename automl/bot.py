# -*- coding: utf-8 -*-
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S: %p') # show DateTime in logger
logger = logging.getLogger(__name__)

import traceback # debug trackback

class Bot:

    from preprocessing_stock import Stock_Preprocessing
    from prediction import Prediction

    predictor = Prediction()

    def __init__(self, debug=False):
        logger.info('Init class Bot ...') # DEBUG

        self.preprocessor = self.Stock_Preprocessing()

        logger.info('... Init class Bot done') # DEBUG

    def get_stock_history(self, stock_ids=[], period='max', start='', end=''):
        ''' return stocks history
            params: (string/list) @stock_ids, e.g. stock_ids='NVDA', stock_ids=['NVDA']
        '''
        data = []

        if not isinstance(stock_ids, list):
            stock_ids = [stock_ids]

        data = self.preprocessor.load_data(stock_ids=stock_ids, period=period, start=start, end=end)

        return data

def test():
    bot = Bot()

    nvda_data = bot.get_stock_history(stock_ids='NVDA')
    print(type(nvda_data))

if __name__ == '__main__':
    test()