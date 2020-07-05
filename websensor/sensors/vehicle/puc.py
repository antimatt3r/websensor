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

from sensors.basesensor import BaseSensor, CaptchaError, LoginError

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://passbook.epfindia.gov.in',
    'passbook': '/MemberPassBook/passbook',
    'captcha': '/MemberPassBook/Login',
    'login': '/MemberPassBook/passbook/api/ajax/checkLogin',
}
TEXT_MAPPING = {
    'TOTAL EE BALANCE': 'Employee',
    'TOTAL ER BALANCE': 'Employer',
    'TOTAL BALANCE (as on date)': 'Total',
}
# This string is used as a suffix and prefix for encoding the password
PASSWORD_ENC_STRING = "kr9rk"


class PfWebSensor(BaseSensor):
    def download_captcha(self, url):
        logger.info(f"Downloading captcha to {self.captcha_image}")
        self.get(url)
        image = self.soup.find(id='captcha_id')['src'].split('base64,')[1]
        with open(self.captcha_image, 'wb') as ifd:
            ifd.write(base64.b64decode(image))

    def encode_password(self, password):
        md5 = hashlib.md5()
        md5.update(password.encode('utf-8'))
        sha512 = hashlib.sha512()
        sha512.update((PASSWORD_ENC_STRING + md5.hexdigest() +
                       PASSWORD_ENC_STRING).encode('utf-8'))
        return sha512.hexdigest()

    def process_captcha(self, captcha):
        captcha = re.sub(r'[^0-9]+$', '', captcha)
        captcha = re.sub(r'^[^0-9]+', '', captcha)
        match = re.match(r'^\d+\s*[/*+-]\d+$', captcha)
        if not match:
            raise CaptchaError(f"Unable to solve captcha: {captcha}")
        result = eval(captcha)
        return result


def main(args) -> dict:
    """ Execute the command.

    :param name: name to use in greeting
    """
    output = {}
    sensor = PfWebSensor('vehicle/puc')

    def get_details(vregn, vfuel):
        url = 'http://etc.karnataka.gov.in/ReportingUser/Scgr1.aspx'

        s = requests.Session()
        r = s.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        soup.find_all('input')

        view_state = soup.find(id='__VIEWSTATE')['value']
        view_state_generator = soup.find(id='__VIEWSTATEGENERATOR')['value']
        event_validation = soup.find(id='__EVENTVALIDATION')['value']

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }

        data = {
            'Sreg': vregn,
            #    'Sreg': 'ka01hb2496',
            'Veh_Type': vfuel,
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_state_generator,
            '__EVENTVALIDATION': event_validation,
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            'Button1': 'Search',
        }
        r = s.post(url, data=data)
        s2 = BeautifulSoup(r.text, 'html.parser')

        table = get_table(s2.find_all('table'))
        if not table:
            LOGGER.debug("No details for {}".format(vregn))
            return {}
        results = parse_table(table)
        latest_results = sorted(results.values(), key=lambda x: parse(x['ValidDate']))[-1]
        latest_results['Expiry'] = dateparser.parse(latest_results['ValidDate']).strftime('%F')
        return latest_results

    return output

def short(args) -> None:
    table = Texttable()
    output = main(args)
    header = ["PF Account", "Employee", "Employer", "Total"]
    table.header(header)
    for account, values in output['balance'].items():
        row = [account]
        for type_ in header[1:]:
            row.append(values[type_])
        table.add_row(row)
    print(table.draw())
#    out = main(args)
