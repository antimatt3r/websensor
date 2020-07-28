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
    'logoff': '/CRA/'
}


class NpsSensor(BaseSensor):
    def download_captcha(self, url):
        self.captcha_image = os.environ['HOME'] + '/tmp/nps.jpg'
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
        return result

    @retry(CaptchaError, tries=3)
    def solve_captcha(self, url):
        self.download_captcha(url)

        custom_config = r'--oem 3 --psm 6 -c ' \
                        r'tessedit_char_whitelist=0123456789+-='
        image = Image.open(self.captcha_image).convert('L')
        image = image.filter(ImageFilter.MedianFilter())
        image = image.point(lambda x: 0 if x < 140 else 255)
        captcha = pytesseract.image_to_string(image, config=custom_config)
        logger.debug(f"Found Captcha: {captcha}")
        result = self.process_captcha(captcha)
        return result

    def get_id(self):
        if "Please enter correct captcha code" in self.response.text:
            haha
        lines = self.response.text.split('\n')
        PP([x for x in lines if 'var totalurl=' in x])
        print(len(lines))
        urllines = [x for x in lines if 'var totalurl=' in x]
        print(urllines)
        urlline = urllines[0]
        match = re.match(r'.*\?ID=([\d-]+).*', urlline)
        if not match:
            raise Exception("Cannot get ID")
        return match.groups()[0]


'''
curl 'https://cra-nsdl.com/CRA/LogonPwd.do;jsessionid=DB1D999CFF9FE59E0670338DEA4E4728.Ghi456' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Cookie: JSESSIONID=DB1D999CFF9FE59E0670338DEA4E4728.Ghi456; cra-nsdl_cookie=2718091530.47873.0000' \
  --data-raw 'userID=XX&password=YY&subCaptchaVal=43' \
  --compressed
'''

'''
curl 'https://cra-nsdl.com/CRA/SOTViewOnload.do?ID=1575258027&getName=SOT%20CG-SG%20Transaction%20Details' \
  -H 'Cookie: JSESSIONID=BE8E470DEA669B26AE5E2809B14C9E3A.Abc123; RandomNumber=223674552; sessionid=BE8E470DEA669B26AE5E2809B14C9E3A.Abc123; cra-nsdl_cookie=906152202.47873.0000' \
  --compressed
'''

'''
curl 'https://cra-nsdl.com/CRA/SOTViewDtls.do?ID=-1282619975&getName=SOT%20CG-SG%20Transaction%20Details' \
  -H 'Cookie: JSESSIONID=BE8E470DEA669B26AE5E2809B14C9E3A.Abc123; sessionid=BE8E470DEA669B26AE5E2809B14C9E3A.Abc123; RandomNumber=-1893656046; cra-nsdl_cookie=906152202.47873.0000' \
  --compressed
'''

'''
curl 'https://cra-nsdl.com/CRA/Log-Off.do?ID=-1282619975&getName=Log-Off' \
  -H 'Cookie: JSESSIONID=BE8E470DEA669B26AE5E2809B14C9E3A.Abc123; sessionid=BE8E470DEA669B26AE5E2809B14C9E3A.Abc123; RandomNumber=-1893656046; cra-nsdl_cookie=906152202.47873.0000' \
  --compressed
'''

def drop_to_shell(vars):
    import code
    try:
        import readline
        import rlcompleter
        historyPath = os.path.expanduser("~/.pyhistory")
        if os.path.exists(historyPath):
                readline.read_history_file(historyPath)
        readline.parse_and_bind('tab: complete')
    except:
        pass
    code.interact(vars)

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

    @retry(CaptchaError, tries=1)
    def solve_captcha():
        captcha = sensor.solve_captcha(URLS['login'])
        if captcha > 100:
            logger.info(f"Suspecting the solved captcha ({captcha})")
            raise CaptchaError
        return captcha

    @retry(CaptchaError, tries=3, delay=5)
    def login():
        captcha = solve_captcha()
        logger.info(f"Captcha = {captcha}")
        login_url = URLS['login'] + ';' + sensor.session.cookies['JSESSIONID']
        data = {
            'userID': sensor.credentials['username'],
            'password': sensor.credentials['password'],
            'subCaptchaVal': captcha,
        }
        # Lets login
        sensor.post(url=login_url, data=data)
        if sensor.soup.find('div', {'class': 'login-tab'}):
            sensor.dump_html('login-error.html')
    #        if 'Please enter correct captcha code' in sensor.response.text:
            raise CaptchaError("Captcha was not validated")
        else:
            print("*****************")

    logger.info("Logging in now ..")
#    login()
#    sensor.dump_html('login-success.html')
##    if not sensor.soup.find('input', {'id': 'logout'}):
##        logger.critical("Writing html")
##        raise LoginError(f"Login did not work")
#    id = sensor.get_id()
#    url = f"/CRA/SOTAccountDetails.do?ID={id}&getName=SOT%20Account%20Details"
#    sensor.get(url)
#    sensor.dump_html('account.html')
    sensor.read_html('account.html')

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

    return output


def short(args) -> None:
    table = Texttable()
    output = main(args)
    pran = list(output.values())[0]['PRAN Number']
    date = list(output.values())[0]['Date']
    header = [f"NPS {pran} ({date})", "Percentage", "Units", "NAV", "Value"]
    table.header(header)
    table.set_max_width(0)
    for scheme, scheme_data in output.items():
        row = [scheme,
               scheme_data['Percentage'],
               scheme_data['Total Units'].replace(',', ''),
               scheme_data['NAV (Rs.)'].replace(',', ''),
               scheme_data['Amount (Rs.)'].replace(',', '')]
        table.add_row(row)
    print(table.draw())
#    out = main(args)
