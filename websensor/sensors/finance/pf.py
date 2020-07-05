""" Implement the vehicle command.

"""
import hashlib
import pprint
import re
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


class PfSensor(BaseSensor):
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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
    }
    sensor = PfSensor('finance/pf', URLS['base'], headers=headers)

    captcha = sensor.solve_captcha(URLS['captcha'])
    logger.info(f"Captcha = {captcha}")

    logger.info("Logging in now ..")
    data = {
        'username': sensor.credentials['username'],
        'password': sensor.encode_password(sensor.credentials['password']),
        'captcha': captcha,
    }

    # Lets login
    sensor.post(url=URLS['login'], data=data)

    # Lets get the required data
    logger.info("Getting the passbook page ..")
    sensor.get(URLS['passbook'])
    if not sensor.soup.find('input', {'id': 'logout'}):
        raise LoginError(f"Login did not work for username {data['username']}")

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
