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
    def _extract_years(self):
        selector = 'select#verbaindenizatoria_ano option'
        return [
            option['value']
            for option in self.soup.select(selector)
            if option['value']
        ]

    def _extract_months(self):
        selector = 'select#verbaindenizatoria_mes option'
        return [
            option['value']
            for option in self.soup.select(selector)
            if option['value']
        ]

    def _extract_politicians(self):
        selector = 'select#transparencia_parlamentar option'
        return [
            option['value']
            for option in self.soup.select(selector)
            if option['value']
        ]

    def _extract_form_data(self, v=False, vv=False):
        if v: print('')
        if v: print('[*] Fetching page...', end='')
        self.fetch()
        if v: print('OK', '\n')

        if v: print('[*] Parsing result...', end='')
        self.parse()
        if v: print('OK', '\n')

        self.data = {
            'form_data': {
                'years': self._extract_years(),
                'months': self._extract_months(),
                'politicians': self._extract_politicians(),
            },
        }

        if vv:
            print('[+] Input data:', '\n')
            print(self.data['form_data'])

        if v: print('')

    def _extract_report_urls(self, year, month, politician=None):
        if politician:
            for a in self.soup.select('td a'):
                if not a.get('href'):
                    continue

                self.data['query_result'][year][month][politician].append({
                    'description': str(a.string).strip(),
                    'href': a.get('href', ''),
                })
        else:
            for h2 in self.soup.select('h2.my-2'):
                if not h2.string:
                    continue

                politician = str(h2.string)
                self.data['query_result'][year][month][politician] = self.data['query_result'][year][month].get(politician, [])

                table = h2.find_next_sibling('table')
                if not table:
                    continue

                for a in table.select('td a'):
                    if not a.get('href'):
                        continue

                    self.data['query_result'][year][month][politician].append({
                        'description': str(a.string).strip(),
                        'href': a.get('href', ''),
                    })

    def _query_indemnity_costs(self, years, months, politicians=None, v=False, vv=False):
        """Query indemnity costs ("Consultar verbas indenizatórias")

        Arguments:
        years -- a list containing years
        months -- a list containing months
        politicians -- a list containing politicians (not required)
        v -- verbosity
        vv -- more verbosity
        """
        self.data['query_result'] = self.data.get('query_result', {})
        params = { 'transparencia.tipoTransparencia.codigo': '14' }

        for year in years:
            self.data['query_result'][year] = self.data['query_result'].get(year, {})

            for month in months:
                self.data['query_result'][year][month] = self.data['query_result'][year].get(month, {})

                params.update({
                    'transparencia.ano': year,
                    'transparencia.mes': month,
                })

                if politicians:
                    for politician in politicians:
                        self.data['query_result'][year][month][politician] = self.data['query_result'][year][month].get(politician, [])

                        try:
                            if v: print(f'[*] Fetching reports for {politician} ({year}/{month})...', end='')

                            params.update({ 'transparencia.parlamentar': politician })

                            self.fetch(method='POST', data=params)
                            self.parse()

                            self._extract_report_urls(year, month, politician)

                            if v: print('OK')
                        except Exception as e:
                            if v:
                                print(f'[-] Error fetching reports for {politician} ({year}/{month}) :(')
                else:
                    try:
                        if v: print(f'[*] Fetching reports for {year}/{month}...', end='')

                        self.fetch(method='POST', data=params)
                        self.parse()

                        self._extract_report_urls(year, month)

                        if v: print('OK')
                    except Exception as e:
                        if v:
                            print(f'[-] Error fetching reports for {year}/{month} :(')

    def start_scraping(self, v=False, vv=False):
        """This is where all the scraping should start

        Arguments:
        v -- verbosity
        vv -- more verbosity
        """
        super().start_scraping()

        self._extract_form_data(v=v, vv=vv)

        self._query_indemnity_costs(
            # years=self.data['form_data']['years'],
            # months=self.data['form_data']['months'],
            # politicians=self.data['form_data']['politicians'],

            # years=['2021'],
            # months=['1', '2'],
            # politicians=self.data['form_data']['politicians'][:3],

            years=['2019'],
            months=['1'],
            #politicians=self.data['form_data']['politicians'],

            v=v, vv=vv
        )

        self.is_scraping_done = True


def _main():
    url = 'https://al.to.leg.br/transparencia/verbaIndenizatoria'
    la = LegislativeAssemblyScraper(url)
    la.start_scraping(v=True, vv=True)
    if la.is_scraping_done:
        #print(la.get_result())
        #print(la.get_json())
        la.save_as_json_file('output.json')


if __name__ == '__main__':
    _main()
