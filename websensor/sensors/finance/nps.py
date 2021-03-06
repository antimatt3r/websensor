""" Implement the vehicle command.

"""
import hashlib
import os
import pprint
import re
from time import sleep

from PIL import Image, ImageEnhance, ImageFilter
from bs4 import BeautifulSoup
import base64
import logging
import json

from pytesseract import pytesseract
from retry import retry
from texttable import Texttable

import sensors
from sensors.basesensor import BaseSensor, CaptchaError, LoginError
from utils.utils import clean_text, list_of_lists_to_dict

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://cra-nsdl.com/',
    'captcha': '/CRA/',
    'login': '/CRA/LogonPwd.do',
    'logoff': '/CRA/Log-Off.do?ID={id}&getName=Log-Off',
    'account_details': "/CRA/SOTAccountDetails.do?ID={id}&getName=SOT%20"
                       "Account%20Details",
}


class NpsSensor(BaseSensor):
    def download_captcha(self, url):
        logger.info(f"Downloading captcha to {self.captcha_image}")
        self.get(url)
        image = self.soup.find(id='captcha').img['src'].split('base64,')[1]
        with open(self.captcha_image, 'wb') as ifd:
            ifd.write(base64.b64decode(image))

    def process_captcha(self, captcha):
        captcha = re.sub(r'[^0-9]+$', '', captcha)
        captcha = re.sub(r'^[^0-9]+', '', captcha)
        captcha.replace('=', '')
        match = re.match(r'^\d+\s*[/*+-]\d+$', captcha)
        if not match:
            raise CaptchaError(f"Unable to solve captcha: {captcha}")
        result = eval(captcha)
        logger.debug(f"Solved captcha = {result}")
        if result > 100:
            logger.info(f"Suspecting the solved captcha ({captcha})")
            raise CaptchaError("Suspecting the solved captcha %s", captcha)
        return result

    def solve_captcha(self):
        custom_config = r'--oem 3 --psm 6 -c ' \
                        r'tessedit_char_whitelist="0123456789+-="'
        image = Image.open(self.captcha_image).convert('L')
        image = image.filter(ImageFilter.MedianFilter())
        image = image.point(lambda x: 0 if x < 140 else 255)
        image.save(self.captcha_image.replace('.jpg', '-edited.jpg'))
        captcha = pytesseract.image_to_string(image, config=custom_config)
        logger.debug(f"Found Captcha: {captcha}")
        if not captcha.endswith("="):
            match = re.match(r'^(\d+[^\d]\d)\d?$', captcha)
            if match:
                logger.info("Captcha does not end with '=', trying to skip"
                            "the last digit")
                captcha = match.groups()[0]
            else:
                raise CaptchaError(
                    "Did not seem to get the captcha right ({})".format(
                        captcha))
        result = self.process_captcha(captcha)
        return result

    def get_id(self):
        if "Please enter correct captcha code" in self.response.text:
            raise LoginError("Cannot fetch ID, captcha does not seem ok")
        lines = self.response.text.split('\n')
        urllines = [x for x in lines if 'var totalurl=' in x]
        urlline = urllines[0]
        match = re.match(r'.*\?ID=([\d-]+).*', urlline)
        if not match:
            raise Exception("Cannot get ID")
        return match.groups()[0]


def main(args) -> dict:
    """ Execute the command.

    :param name: name to use in greeting
    """
    output = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://cra-nsdl.com/CRA/',
    }
    sensor = NpsSensor('finance/nps', URLS['base'], headers=headers,
                       creds=True)

    @retry(CaptchaError, tries=5, delay=5)
    def login():
        sensor.download_captcha(URLS['login'])
        captcha = sensor.solve_captcha()
        logger.info(f"Captcha = {captcha}")
        login_url = URLS['login'] + ';' + sensor.session.cookies['JSESSIONID']
        data = {
            'userID': sensor.credentials['username'],
            'password': sensor.credentials['password'],
            'subCaptchaVal': captcha,
        }
        # Lets login
        sensor.post(url=login_url, data=data)
        if "Your Password has expired." in sensor.response.text:
            raise LoginError("The Password has expired")
        sensor.dump_html('login-out.html')
        if sensor.soup.find('div', {'class': 'login-tab'}):
#            sensor.dump_html('login-error.html')
    #        if 'Please enter correct captcha code' in sensor.response.text:
            raise CaptchaError("Captcha was not validated")
        logger.info("Success!!")

    logger.info("Logging in now ..")
    login()
    if not "Welcome Subscriber" in sensor.soup.text:
        sensor.dump_html("login-error.html")
        raise LoginError(f"Login did not work")
 #   sensor.dump_html('login-success.html')
    id = sensor.get_id()
    sensor.get(URLS['account_details'].format(id=id))
#    sensor.dump_html('account.html')
#    sensor.read_html('account.html')

    def parse_table(soup):
        table = {}
        name = clean_text(soup.find('tbody').find('tr').text)
        table[name] = []
        if 'No Record Found' in soup.text:
            return {}
        headers = [
            clean_text(x.text)
            for x in soup.find('tbody').find_all('tr')[1].find_all('td')
        ]
        table[name].append(headers)
        for row in soup.find_all('tbody')[1].find_all('tr'):
            if 'Total' in row.text:
                # Lets skip the row which gives the total
                continue
            values = [clean_text(x.text) for x in row.find_all('td')]
            if len(values) < len(headers):
                # HACK: Assuming that if less columns than expected, left
                # side cells are merged
                values.insert(0, table[name][1][0])
            table[name].append(values)
        return table

    rawdata = {}
    for t in sensor.soup.find_all('table', {'class': 'table-newnorow'}):
        table_data = parse_table(t)
        rawdata.update(table_data)

    prefs = list_of_lists_to_dict(rawdata['Current Scheme Preference'],
                                  "Scheme Details")
    summary = list_of_lists_to_dict(
        rawdata['Account Summary For Current Schemes'], "Scheme Name")

    date = clean_text(sensor.soup.find(id='stddate').span.text)
    pran = clean_text(sensor.soup.find(id='pranno').text)
    for scheme, scheme_data in summary.items():
        scheme_data['Percentage'] = prefs[scheme]['Percentage']
        scheme_data['Date'] = date
        scheme_data['PRAN Number'] = pran
        output[scheme] = scheme_data

    logger.info("Logging off ..")
    sensor.get(URLS['logoff'].format(id=sensor.get_id()))
    return output


def short(args) -> None:
    table = Texttable()
    output = main(args)
    pran = list(output.values())[0]['PRAN Number']
    date = list(output.values())[0]['Date']
    header = [f"NPS {pran} ({date})", "Percentage", "Units", "NAV", "Value"]
    table.header(header)
    table.set_cols_dtype(['t', 't', 't', 't', 't'])
    table.set_max_width(0)
    for scheme, scheme_data in output.items():
        row = [scheme,
               scheme_data['Percentage'],
               scheme_data['Total Units'].replace(',', ''),
               scheme_data['NAV (Rs.)'].replace(',', ''),
               scheme_data['Amount (Rs.)'].replace(',', '')]
        table.add_row(row)
    print(table.draw())
