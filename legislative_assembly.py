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

    def _prepare_to_get_data_from_form(self):
        """Initializes a dict to store data from the HTML form"""

        # Fetches the page for the first
        # time just to get the list of years
        self.fetch()
        self.parse()

        self.data = {
            'formData': {},
        }

        for year in self._extract_years():
            self.data['formData'].update({
                year: {
                    'months': [],
                    'politicians': [],
                    'politicianCount': 0,
                },
            })

    def _get_params(self):
        return {
            'transparencia.tipoTransparencia.codigo': '14',
            'transparencia.ano': '',
            'transparencia.mes': '',
            'transparencia.parlamentar': '',
        }

    def _extract_data_from_form(self):
        """For each year, gets the months and politicians"""

        params = self._get_params()

        for year in self.data['formData'].keys():
            params.update({ 'transparencia.ano': year })

            self.fetch(method='POST', data=params)
            self.parse()

            months = self._extract_months()
            politicians = self._extract_politicians()

            self.data['formData'].update({
                year: {
                    'months': months,
                    'politicians': politicians,
                    'politicianCount': len(politicians),
                },
            })

    def _extract_form_data(self, v=False, vv=False):
        self._prepare_to_get_data_from_form()
        self._extract_data_from_form()

    def _extract_urls_by_month(self, year, month, politicians=None):
        for h2 in self.soup.select('h2.my-2'):
            if not h2.string:
                continue

            politician = str(h2.string)
            if politicians and politician not in politicians:
                continue

            self.data['queryResult'][year][month][politician] = self.data['queryResult'][year][month].get(politician, [])

            table = h2.find_next_sibling('table')
            if not table:
                continue

            for a in table.select('td a'):
                if not a.get('href'):
                    continue

                self.data['queryResult'][year][month][politician].append({
                    'description': str(a.string).strip(),
                    'href': a.get('href', ''),
                })

    def _extract_urls_by_politician(self, year, month, politician):
        for a in self.soup.select('td a'):
            if not a.get('href'):
                continue

            self.data['queryResult'][year][month][politician].append({
                'description': str(a.string).strip(),
                'href': a.get('href', ''),
            })

    def _query_indemnity_costs(self, years=None, months=None, politicians=None, fetch_one_by_one=False, v=False, vv=False):
        """Query indemnity costs ("Consultar verbas indenizatórias")

        Arguments:
        years -- a list containing years (not required)
        months -- a list containing months (not required)
        politicians -- a list containing politicians (not required)
        fetch_one_by_one -- if True, makes one request for each
                            politician (which is not recommended
                            as the overall completion time will
                            be long)
        v -- verbosity
        vv -- more verbosity
        """
        if isinstance(years, (list, tuple)):
            years = [str(year) for year in years]

        if isinstance(months, (list, tuple)):
            months = [str(month) for month in months]

        self.data['queryResult'] = self.data.get('queryResult', {})
        params = { 'transparencia.tipoTransparencia.codigo': '14' }

        for year in self.data['formData'].keys():
            if years and year not in years:
                continue
            self.data['queryResult'][year] = self.data['queryResult'].get(year, {})
            for month in self.data['formData'][year]['months']:
                if months and month not in months:
                    continue
                self.data['queryResult'][year][month] = self.data['queryResult'][year].get(month, {})
                params.update({
                    'transparencia.ano': year,
                    'transparencia.mes': month,
                })
                if fetch_one_by_one:
                    for politician in self.data['formData'][year]['politicians']:
                        if politicians and politician not in politicians:
                            continue
                        self.data['queryResult'][year][month][politician] = self.data['queryResult'][year][month].get(politician, [])
                        params.update({ 'transparencia.parlamentar': politician })
                        try:
                            self.fetch(method='POST', data=params)
                            self.parse()
                        except:
                            pass
                        self._extract_urls_by_politician(year, month, politician)
                else:
                    # Passing an empty string will bring URLs for all
                    # politicians according to the given year and month
                    params.update({ 'transparencia.parlamentar': '' })
                    try:
                        self.fetch(method='POST', data=params)
                        self.parse()
                    except:
                        pass
                    self._extract_urls_by_month(year, month, politicians)

    def start_scraping(self, v=False, vv=False):
        """This is where all the scraping should start

        Arguments:
        v -- verbosity
        vv -- more verbosity
        """
        super().start_scraping()

        self._extract_form_data(v=v, vv=vv)

        self._query_indemnity_costs(
            # years=['2019'],
            # months=['1'],
            # politicians=self.data['formData']['2019']['politicians'][:5],

            years=[2019],
            months=[3],
            politicians=self.data['formData']['2019']['politicians'][:5],
            fetch_one_by_one=True,

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
