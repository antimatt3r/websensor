""" Implement the vehicle command.

"""
import pprint
import re

import logging
from texttable import Texttable

from sensors.basesensor import BaseSensor

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://myaccount.dbroadband.in',
    'login': '/login/process',
}


class DbroadbandSensor(BaseSensor):
    pass


def main(args) -> dict:
    """ Execute the command.

    :param name: name to use in greeting
    """
    output = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }
    sensor = DbroadbandSensor('utilities/dbroadband', headers=headers, base_url=URLS['base'], creds=True)

    data = {
        'unme': sensor.credentials['username'],
        'passd': sensor.credentials['password']
    }

    sensor.post(URLS['login'], data=data)

    def _get_subscription(soup):
        subscription_data = soup.find('span', {'class': 'counter'}).text.replace('\n', '')
        return {
            'Days Left': int(re.sub(r'(\d+).*', r'\1', subscription_data))
        }

    def _get_fup(soup):
        group_items = soup.find_all('li', {'class': 'list-group-item'})
        fup = {}
        for gi in group_items:
            value = gi.span.extract().text.strip().replace(',', '')
            key = f'{gi.text.strip()} ({value.split(" ")[1]})'
            fup[key] = float(value.split(" ")[0])
        return fup

    def get_data(soup):
        wbs = soup.find_all('div', {'class': 'white-box'})
        data = {}
        for wb in wbs:
            h3 = wb.find('h3', {'class': 'box-title'})
            span = h3.find('span')
            a = h3.find('a')
            type_ = None
            if span:
                h3.span.extract()
                type_ = h3.text.strip()
            elif a:
                h3.a.extract()
                type_ = h3.text.strip()
            else:
                type_ = h3.text.strip()
            if type_ == 'Subscription':
                data.update(_get_subscription(wb))
            elif type_ == 'FUP Data Info':
                data.update(_get_fup(wb))
    #        elif type_ == 'Account Info':
    #            data.update(_get_account_info(wb))
    #        else:
    #            print(type_)
        return data

    outputs = get_data(sensor.soup)

    return outputs

def short(args) -> None:
    table = Texttable()
    output = main(args)
    header = ["DBroadband - Days Left", "Data Left (GB)"]
    table.header(header)
    table.add_row(
        [output["Days Left"],
         f"{output['Data Remaning (GB)']} / {output['Total Data (GB)']}"])
    print(table.draw())
#    out = main(args)
