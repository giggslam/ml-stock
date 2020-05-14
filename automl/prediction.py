# -*- coding: utf-8 -*-
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S: %p') # show DateTime in logger
logger = logging.getLogger(__name__)
import traceback # debug trackback
import sys

class Prediction:
    def __init__(self, debug=False):
        logger.info('Init class Prediction ...') # DEBUG

        logger.info('... Init class Prediction done') # DEBUG

def test():
    pass

if __name__ == '__main__':
    test()