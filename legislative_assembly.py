#!/usr/bin/env python
"""Provides a web scraping class called LegislativeAssemblyScraper

LegislativeAssemblyScraper is a subclass that extends the Scraper
base class and is designed to be used in a very specific web scraping
use case.

This class scrapes data related to transparency and accountability
from the page of the Legislative Assembly of Tocantins ("Assembleia
Legislativa do Tocantins"), a website of the Brazilian government.
"""

from scraper import Scraper


__author__     = 'Dartz'
__copyright__  = 'Copyright 2021'
__credits__    = ['Dartz']
__license__    = 'MIT'
__version__    = '0.1.0'
__maintainer__ = 'Dartz'
__email__      = 'samuel.viveiros@gmail.com'
__status__     = 'Development'


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
