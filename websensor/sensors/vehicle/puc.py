""" Implement the vehicle command.

"""
import hashlib
import pprint
import re

import requests
from bs4 import BeautifulSoup
import base64
import logging
import json
from texttable import Texttable
import dateparser
from dateutil.parser import parse

from sensors.basesensor import BaseSensor, CaptchaError, LoginError

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'http://etc.karnataka.gov.in',
}


class PucSensor(BaseSensor):
    pass


def parse_table(table):
    results = {}
    headers = [x.text for x in table.find_all('th')]
    for row in table.find_all('tr')[1:]:
        values = [x.text for x in row.find_all('td')]
        row_data = dict(zip(headers, values))
        row_data[u'ValidDate_ts'] = parse(row_data['ValidDate']).strftime('%s')
        results[row_data['Pucc No']] = dict(zip(headers, values))
    return results

def get_table(tables):
    correct_table = None
    logger.debug('Finding table ..')
    for table in tables:
        try:
            headers = table.find_all('tr')[0].find_all('th')[0]
            if table.find('table'):
                # Nested tables! Skip the upper layers
                continue
            return table
        except (AttributeError, IndexError):
            pass
    return correct_table


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
    sensor = PucSensor('vehicle/puc', headers=headers, base_url=URLS['base'], creds=False)

    url = '/ReportingUser/Scgr1.aspx'
    sensor.get(url)

    view_state = sensor.soup.find(id='__VIEWSTATE')['value']
    view_state_generator = sensor.soup.find(id='__VIEWSTATEGENERATOR')['value']
    event_validation = sensor.soup.find(id='__EVENTVALIDATION')['value']

    vehicles = []
    input_vehicles = args.args if args.args else sensor.inputs["vehicles"]
    for vehicle in input_vehicles:
        if '/' in vehicle:
            vehicles.append(vehicle.split('/'))
            vehicles[-1][1] = vehicles[-1][1].upper()
        else:
            vehicles.append([vehicle, 'P'])
            vehicles.append([vehicle, 'D'])
    if not vehicles:
        vehicles = sensor.config

    def get_detail(registration, fuel_type):
        data = {
            'Sreg': registration,
            'Veh_Type': fuel_type,
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_state_generator,
            '__EVENTVALIDATION': event_validation,
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            'Button1': 'Search',
        }
        sensor.post(url, data=data)

        table = get_table(sensor.soup.find_all('table'))
        if not table:
            logger.debug("No details for {}".format(data['Sreg']))
            return {}
        results = parse_table(table)
        latest_results = sorted(results.values(), key=lambda x: parse(x['ValidDate']))[-1]
        latest_results['Expiry'] = dateparser.parse(latest_results['ValidDate']).strftime('%F')
        return latest_results

    outputs = {}
    for vehicle, fuel_type in vehicles:
        data = get_detail(vehicle, fuel_type)
        if data:
            outputs[vehicle] = data

    return outputs

def short(args) -> None:
    table = Texttable()
    output = main(args)
    header = ["Vehicle Regn", "Make/Model", "Expiry of PUC"]
    table.header(header)
    for vehicle, details in output.items():
        row = [vehicle.upper()]
        row.append((details.get('Make', '') + '/' + details.get('Model', '')).strip('/'))
        row.append(details['Expiry'])
        table.add_row(row)
    print(table.draw())
#    out = main(args)
