#!/usr/bin/env python
"""Provides Scraper and LegislativeAssemblyScraper classes

Scraper is a generic class for web scraping, powered by
'beautifulsoup4' and 'requests' modules.

LegislativeAssemblyScraper is a specialized Scraper class designed
specifically to scrap data related to the Assembleia Legislativa do
Tocantins (Brazil)'s transparency and accountability.
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
    """Generic class for web scraping"""

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
        self.is_scrap_done = False

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

    def start_scraping(self):
        self.is_scrap_done = False

    def get_result(self):
        if not self.is_scrap_done:
            raise Exception('Web scraping is not done yet')

        return self.data

    def get_json(self):
        return json.dumps(self.get_result(), indent=2)

    def save_as_json_file(self, filename):
        with open(filename, 'w') as fd:
            fd.write(self.get_json())


class LegislativeAssemblyScraper(Scraper):
    """Page scraper for Assembleia Legislativa do Tocantins

    Page target: Transparência -> Verbas Indenizatórias
    URL: https://al.to.leg.br/transparencia/verbaIndenizatoria
    """
    def _get_years(self):
        selector = 'select#verbaindenizatoria_ano option'
        return [
            option['value']
            for option in self.soup.select(selector)
            if option['value']
        ]

    def _get_months(self):
        selector = 'select#verbaindenizatoria_mes option'
        return [
            option['value']
            for option in self.soup.select(selector)
            if option['value']
        ]

    def _get_politicians(self):
        selector = 'select#transparencia_parlamentar option'
        return [
            option['value']
            for option in self.soup.select(selector)
            if option['value']
        ]

    def _get_politician_reports(self):
        selector = 'td a'
        return [
            anchor['href']
            for anchor in self.soup.select(selector)
            if anchor['href']
        ]

    def _extract_input_data(self, v=False, vv=False):
        if v: print('')
        if v: print('[*] Fetching page...', end='')
        self.fetch()
        if v: print('OK', '\n')

        if v: print('[*] Parsing result...', end='')
        self.parse()
        if v: print('OK', '\n')

        self.data = {
            'input_data': {
                'years': self._get_years(),
                'months': self._get_months(),
                'politicians': self._get_politicians(),
            },
        }

        if vv:
            print('[+] Input data:', '\n')
            print(self.data['input_data'])

        if v: print('')

    def _extract_politician_data(self, year, month, politician, v=False, vv=False):
        if v: print(f'[*] Fetching reports for {politician} ({year}/{month})...', end='')
        self.fetch(method='POST', data={
            'transparencia.tipoTransparencia.codigo': '14',
            'transparencia.ano': year,
            'transparencia.mes': month,
            'transparencia.parlamentar': politician,  # if omitted, it'll bring everybody
        })

        self.parse()

        self.data['output_data'] = self.data.get('output_data', {})
        self.data['output_data'][year] = self.data['output_data'].get(year, {})
        self.data['output_data'][year][month] = self.data['output_data'][year].get(month, [])
        self.data['output_data'][year][month].append({
            'politician': politician,
            'reports': self._get_politician_reports(),
        })

        if v: print('OK')

    def start_scraping(self, v=False, vv=False):
        super().start_scraping()

        self._extract_input_data(v=v, vv=vv)

        # _TODO_ This code is generating about 1500 requests. Refactor code for performance.
        for year in self.data['input_data']['years']:
            for month in self.data['input_data']['months']:
                for politician in self.data['input_data']['politicians']:
                    try:
                        self._extract_politician_data(year, month, politician, v=v, vv=vv)
                    except Exception as e:
                        if v:
                            print(f'[-] Error fetching reports for {politician} ({year}/{month}) :(')

        self.is_scrap_done = True


def _main():
    url = 'https://al.to.leg.br/transparencia/verbaIndenizatoria'
    la = LegislativeAssemblyScraper(url)
    la.start_scraping(v=True, vv=True)
    if la.is_scrap_done:
        #print(la.get_result())
        #print(la.get_json())
        la.save_as_json_file('output.json')


if __name__ == '__main__':
    _main()
