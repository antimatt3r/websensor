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

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://cra-nsdl.com/',
    'captcha': '/CRA/',
    'login': '/CRA/LogonPwd.do',
    'logoff': '/CRA/'
}
TEXT_MAPPING = {
    'TOTAL EE BALANCE': 'Employee',
    'TOTAL ER BALANCE': 'Employer',
    'TOTAL BALANCE (as on date)': 'Total',
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
    drop_to_shell(dict(globals(), **locals()))
    sdfj
    sensor = NpsSensor('finance/nps', URLS['base'], headers=headers,
                       creds=True)

    @retry(CaptchaError, tries=1)
    def solve_captcha():
        captcha = sensor.solve_captcha(URLS['login'])
        if captcha > 100:
            logger.info(f"Suspecting the solved captcha ({captcha})")
            raise CaptchaError
        return captcha

    @retry(CaptchaError, tries=3)
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
            logger.critical("Trying again ..")
            sleep(5)
            raise CaptchaError("Captcha was not validated")
        else:
            print("*****************")

    logger.info("Logging in now ..")
    login()
    sensor.dump_html('login-success.html')
#    if not sensor.soup.find('input', {'id': 'logout'}):
#        logger.critical("Writing html")
#        raise LoginError(f"Login did not work")
    PP("DONE")
    id = sensor.get_id()
    url = f"/CRA/SOTAccountDetails.do?ID={id}&getName=SOT%20Account%20Details"
    sensor.get(url)
    sensor.dump_html('account.html')
    done


    # Lets get the required data
    logger.info("Getting the passbook page ..")
    sensor.get(URLS['passbook'])

    h3 = sensor.soup.find('h3').text
    match = re.match(r'\s*Welcome\s*:\s*(.*)\s*\[\s*(\d+)\s*\]', h3)
    output['name'] = match.groups()[0]
    output['uan'] = match.groups()[1]

    logger.debug("Fetching MIDs ..")
    mids = sensor.soup.find(id="selectmid")
    accounts = {}
    for option in mids.find_all('option'):
        if option.attrs['value'] != '0':
            if 'value' in option.attrs:
                accounts[option.text] = option.attrs['value']

    pb_url_line = [x for x in sensor.response.text.split('\n') if '/get-member-passbook' in x][0]
    pb_url = re.sub(r".*'(/passbook/ajax/.*/get-member-passbook).*", r'\1', pb_url_line)

    output['balance'] = {}
    for account, mid in accounts.items():
        output['balance'][account] = {}
        data = {
            'midToken': mid,
            'mid': account,
            'tbl': 'tbl_' + account,
        }
        url = f'/MemberPassBook/{pb_url}'
        sensor.post(url, data=data)
        soup = BeautifulSoup(json.loads(sensor.response.text)[0]['html'], 'html.parser')
        table = soup.find('table', {'class': 'table table-bordered'})
        for row in table.find_all('tr'):
            type_, balance = [x.text for x in row.find_all("td")]
            # Lets remap the keys
            output['balance'][account][TEXT_MAPPING[type_]] = re.sub(r'[^\d]', r'', balance)

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
