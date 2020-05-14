# -*- coding: utf-8 -*-
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S: %p') # show DateTime in logger
logger = logging.getLogger(__name__)

class Preprocessing:
    ''' Preprocessing tasks, 2020-03-23
        e.g. segmentation, remove stopwords ...
    '''
    import os
    import traceback
    import requests, json
    import nltk
    import jieba
    from bs4 import BeautifulSoup
    import re
    from contractions import CONTRACTION_MAP # Contractions ("aren't" >>> "are not")
    import pandas as pd

    jieba_dict_path = 'data/jieba/dict.txt.big'
    jieba_userdict_path = 'data/jieba/userdict.txt'
    jieba_stopwords_path = 'data/jieba/stop_words.txt'
    jieba_stopword_list = []

    def __init__(self, debug=False):
        logger.info('Init class Preprocessing ...') # DEBUG
        self.debug = debug
        self.init_tokenization()
        logger.info('... Init class Preprocessing done') # DEBUG

    def init_tokenization(self):
        # init Jieba
        logger.info('init jieba ...')
        self.jieba.set_dictionary(self.jieba_dict_path) # Set Chinese Traditional
        self.jieba.load_userdict(self.jieba_userdict_path) # Load User Customized Dict
        with open(r'%s' % self.jieba_stopwords_path, 'r', encoding='utf8') as f:
            self.jieba_stopword_list = [line.strip() for line in f]
        self.jieba.initialize() # Init at startup
        logger.info('... init jieba done')

    def is_file_exist(self, file_path=''):
        ''' check if the file exist or not
        '''
        if self.os.path.isfile(file_path):
            return True
        else:
            return False

    def read_file(self, textfile='', mode='str'):
        ''' Read data from text file, 2019-12-09

            input: file path
            return: string / list(one line one item)

            TODO:
                - check file exist or not
        '''
        if mode == 'str': # return string
            data = open(textfile,'r', encoding='utf8').read() # read string from file, return string

        elif mode == 'list': # return list (one line one item)
            with open (textfile, "r", encoding='utf8') as myfile:
                data = myfile.readlines()

        return data

    def read_json_file(self, file_path='data/configs.json'):
        ''' read data from json file, 2020-02-25

            params: <str>file_path
            return: <dict>data
        '''
        try:
            data = {}

            if self.is_file_exist(file_path):
                logger.info(f'read_json_file(), reading data from file_path "{file_path}" ...')
                with open(file_path) as json_file:
                    data = self.json.load(json_file)
        except Exception as e:
            logger.error(e)
        finally:
            logger.info('... read_json_file()') # DEBUG
            return data

    def save_text_list_to_file(self, data=[], file_path='data/text_list.txt'):
        ''' save texts list to file, 2020-02-25
            params: <list><str>data, <str>file_path
        '''
        try:
            logger.info(f'save_text_list_to_file(), list will be saved in {file_path} ...') # DEBUG
            with open(file_path, 'w') as filehandle:
                # store the data as string
                filehandle.writelines(f'{data_item}\n' for data_item in data) # add list item & newline to file
        except Exception as e:
            logger.error(self.traceback.format_exc())
            logger.error(e)
            logger.error(f'save_text_list_to_file(), list cannot save in {file_path}') # DEBUG
        finally:
            logger.info(f'... save_text_list_to_file()') # DEBUG

    def save_dataframe_to_file(self, data:'pd.DataFrame', file_path='data/data.csv'):
        ''' save pandas DataFrame to csv file, 2020-05-06
            params: (DataFrame) @data, e.g. stock closing price
                    (string) @file_path
        '''
        try:
            logger.info(f'save_dataframe_to_file(), DataFrame will be saved in {file_path} ...') # DEBUG
            data.to_csv(file_path, header=True)
        except Exception as e:
            logger.error(self.traceback.format_exc())
            logger.error(e)
            logger.error(f'save_dataframe_to_file(), DataFrame cannot save in {file_path}') # DEBUG
        finally:
            logger.info(f'... save_dataframe_to_file()') # DEBUG

    def clean_text(self, text=''):
        ''' Clean Text (remove extra/special characters), 2019-12-09
        '''
        soup = self.BeautifulSoup(text, "lxml")
        cleaned_text = soup.get_text()

        if self.debug == True: logger.info('clean_text(), cleaned_text: %s' % cleaned_text) #DEBUG
        return cleaned_text

    def case_conversion(self, text='', case='lower'):
        ''' case conversion, 2019-12-09
        '''
        if case == 'lower':
            text = text.lower()
        elif case == 'upper':
            text = text.upper()

        if self.debug == True: logger.info('case_conversion(), %s(): %s' % (case, text))
        return text

    def expand_contractions(self, text, contraction_mapping):
        ''' Contractions, e.g. wasn't >> was not, 2019-12-09

            Example:
            expanded_corpus = [expand_contractions(text, CONTRACTION_MAP)
                                for text in cleaned_corpus]
        '''
        contractions_pattern = self.re.compile('({})'.format('|'.join(contraction_mapping.keys())),
                                        flags=self.re.IGNORECASE|self.re.DOTALL)
        def expand_match(contraction):
            match = contraction.group(0)
            first_char = match[0]
            expanded_contraction = contraction_mapping.get(match)\
                                    if contraction_mapping.get(match)\
                                    else contraction_mapping.get(match.lower())
            expanded_contraction = first_char+expanded_contraction[1:]
            return expanded_contraction

        expanded_text = contractions_pattern.sub(expand_match, text)

        if self.debug == True: logger.info('case_conversion(), text_lower: %s' % text.lower()) #DEBUG
        return expanded_text

    def remove_stopwords(self, words=[]):
        ''' remove stop words (e.g. 的, 。), 2019-12-09
            input: (list) tokenized words
        '''
        words_removed_stopwords = [word for word in words if word not in self.jieba_stopword_list and word.strip('\r\n') != '' and word != ' ']
        return words_removed_stopwords

    def tokenize(self, text='', tokenizer='jieba'):
        ''' tokenize 分詞, 2019-12-09
            input:
                (str) text
                tokenizer: 'jieba' (default) / 'nltk_default' / 'nltk_regex'
            return (list) tokenized words
        '''
        words = []

        # Jieba (Chinese)
        def tokenizer_jieba(text):
            words = self.jieba.lcut(text, cut_all=False)
            return words

        # NLTK default Tokenizer
        def tokenizer_nltk_default(text):
            wt = self.nltk.word_tokenize
            words = wt(text)
            return words

        # RegexpTokenizer
        def tokenizer_nltk_regex(text):
            TOKEN_PATTERN = r'\s+'
            regex_wt = self.nltk.RegexpTokenizer(pattern=TOKEN_PATTERN, gaps=True)
            wt = regex_wt
            words = wt.tokenize(text)
            return words

        if tokenizer == 'jieba':
            words = tokenizer_jieba(text)
        elif tokenizer == 'nltk_default':
            words = tokenizer_nltk_default(text)
        elif tokenizer == 'nltk_regex':
            words = tokenizer_nltk_regex(text)

        if self.debug == True: logger.info('tokenize(), words: %s' % words) #DEBUG
        return words

    def get_intents_from_db(self, agent_id=''):
        ''' get intents from API
        '''
        try:
            logger.info('get_intents_from_db() ...')
            results = {}

            url = 'https://www.chatbot.hk/NLPv2.Intent.api.V3.test.php' # new "required_entities", 2019-09-20
            params = {'Key': '63ebdad609d02ac15a71bde64fb21f8ea43ac513', 'AgentID': agent_id, 'ParentID': 0, 'Status': 1}
            r = self.requests.get(url, params=params)

            results = r.json()
        except Exception as e:
            logger.error(self.traceback.format_exc())
            logger.error(e)
        finally:
            return results

    def get_actual_file_path(self, relative_file_path=''):
        ''' params: Relative File Path, e.g. 'Data/1/intent.json'
            return: FullPath, e.g. '/Home/ubuntu/NLPv3/Data/1/intent.json'
        '''
        curr_dir_path = self.os.path.dirname(self.os.path.abspath(__file__))
        full_path = self.os.path.join(curr_dir_path, relative_file_path)
        return full_path

    def remove_intents_cache_files(self, agent_id=''):
        ''' delete specific files
        '''
        try:
            logger.info('remove_intents_cache_files() ...') # DEBUG
            intent_file = f'data/intents/intents.{agent_id}.json'
            file_to_be_delete = self.get_actual_file_path(intent_file)
            if self.os.path.isfile(file_to_be_delete):
                self.os.unlink(file_to_be_delete)
                logger.warning(f'... removed "{file_to_be_delete}"') # DEBUG
            else:
                logger.warning(f'... {file_to_be_delete} not found, no file deleted') # DEBUG
        except Exception as e:
            logger.error(self.traceback.format_exc())
            logger.error(e)
        finally:
            logger.info('... remove_intents_cache_files()') # DEBUG

    def save_json_file(self, input_data={}, output_file=''):
        ''' dump dict to json file
            params: <dict> json data
        '''
        try:
            logger.info('save_json_file ...') # DEBUG
            # TODO: assurePathExists(output_file) # Create folder if not exist
            output_file = self.get_actual_file_path(relative_file_path=output_file) # convert relative path to full path

            with open(output_file, 'w', encoding='UTF-8') as f:
                self.json.dump(input_data, f)
            logger.info(f'file saved in "{output_file}"')
            logger.info('... save_json_file()')
        except Exception as e:
            logger.error(self.traceback.format_exc())
            logger.error(e)

    def gen_intents_cache_files(self, agent_id=''):
        ''' generate intents file, e.g. 'data/intents/intents.25.json'
        '''
        logger.info('gen_intents_cache_files() ...') # DEBUG

        # Clear existing Intents files (data/intents/intents.xxx.json)
        self.remove_intents_cache_files(agent_id=agent_id)

        results = self.get_intents_from_db(agent_id=agent_id)

        # Root intent
        # TODO: Child intent, Keyword intent (TBR), Fallback intent
        final_results = results['IntentRoot'] if 'IntentRoot' in results else ''
        if final_results:
            cache_file = f'data/intents/intents.{agent_id}.json'
            self.save_json_file(input_data=final_results, output_file=cache_file)


if __name__ == '__main__':
    preprocessor = Preprocessing() # init Preprocessing instance

    # query = '日文章魚怎樣說'
    query = 'this is a testing'

    # tokenization
    tokenized_words = preprocessor.tokenize(query)
    print('tokenized_words: %s' % tokenized_words)

    # remove stop words
    words = preprocessor.remove_stopwords(tokenized_words)
    print('removed stop words: %s' % words)