"""Provides a web scraping base class called Scraper

It is powered by 'beautifulsoup4' and 'requests' modules.
"""

import json
import random

import requests
from bs4 import BeautifulSoup


__author__     = 'Dartz'
__copyright__  = 'Copyright 2021'
__credits__    = ['Dartz']
__license__    = 'MIT'
__version__    = '0.1.0'
__maintainer__ = 'Dartz'
__email__      = 'samuel.viveiros@gmail.com'
__status__     = 'Development'


def merge(dict1, dict2):
    """Returns the merge of dict1 and dict2 but prioritizing dict2's items"""
    return {**dict1, **dict2}


def mergeIf(dict1, dict2):
    """Returns the merge of dict1 and dict2 but prioritizing dict1's items"""
    return {**dict2, **dict1}


class Scraper:
    """Base class for web scraping

    This class is intended to be extended and should not
    be created directly.
    """

    DEFAULT_TIMEOUT = 60.0  # Given in seconds

    fake_user_agents = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',  # Chrome
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36 OPR/74.0.3911.218',  # Opera
        'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0',  # Firefox
    ]

    def __init__(self, url):
        self.url = url

        self.response = None
        self.soup = None
        self.is_scraping_done = False

        # Put all the extracted data in this dictionary
        self.data = {}

    def get_headers(self, custom=None):
        custom = custom or {}

        index = random.randrange(0, len(Scraper.fake_user_agents))
        default = { 'user-agent': Scraper.fake_user_agents[index] }

        return mergeIf(custom, default)

    def has_valid_response(self):
        return isinstance(self.response, requests.models.Response)

    def has_valid_soup(self):
        return isinstance(self.soup, BeautifulSoup)

    def validate_response(self):
        if not self.has_valid_response():
            raise Exception('You have to fetch the page first.')

    def validate_soup(self):
        if not self.has_valid_soup():
            raise Exception('You have to parse the page first.')

    def save_page_to_file(self, filename):
        self.validate_response()

        with open(filename, 'w') as fd:
            fd.write(self.response.text)

    def fetch(self, **kwargs):
        try:
            method = 'GET'
            if 'method' in kwargs:
                method = kwargs['method']
                del kwargs['method']

            kwargs.setdefault('timeout', Scraper.DEFAULT_TIMEOUT)
            kwargs.setdefault('headers', self.get_headers())
            kwargs.setdefault('verify', False)  # Bypass SSL certificate verification

            if method == 'GET':
                self.response = requests.get(self.url, **kwargs)
            elif method == 'POST':
                self.response = requests.post(self.url, **kwargs)
            else:
                raise ValueError('Supported methods: GET, POST')

            # Raises an HTTPError if status code != 200
            self.response.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(str(e))
        except requests.ConnectTimeout as e:
            raise Exception(f'Connection timeout: {str(e)}')
        except requests.ConnectionError as e:
            raise Exception(f'Network issue: {str(e)}')
        except requests.TooManyRedirects as e:
            raise Exception(f'Too many redirects: {str(e)}')
        except Exception as e:
            raise Exception(f'Unknow error: {str(e)}')

        # If we get this far, then everything looks fine :)

    # _TODO_ Error treatments
    def parse(self):
        self.validate_response()
        self.soup = BeautifulSoup(self.response.text, 'lxml')

    def get_result(self):
        if not self.is_scraping_done:
            raise Exception('Web scraping is not done yet')

        return self.data

    def get_json(self):
        return json.dumps(self.get_result(), indent=2)

    def save_as_json_file(self, filename):
        with open(filename, 'w') as fd:
            fd.write(self.get_json())

    def start_scraping(self):
        """This is where all the scraping should start

        This method must be overridden in a subclass
        """
        self.is_scraping_done = False
