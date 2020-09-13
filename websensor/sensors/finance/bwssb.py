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

'''
curl 'https://www.bwssb.gov.in/login.php' \
  -H 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryvgqFkBjlcbgD0lQT' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  --data-binary $'------WebKitFormBoundaryvgqFkBjlcbgD0lQT\r\nContent-Disposition: form-data; name="csrf"\r\n\r\n\r\n------WebKitFormBoundaryvgqFkBjlcbgD0lQT\r\nContent-Disposition: form-data; name="rr_number"\r\n\r\nRRNUMBER\r\n------WebKitFormBoundaryvgqFkBjlcbgD0lQT\r\nContent-Disposition: form-data; name="rr_number_pass"\r\n\r\nPASSWORD\r\n------WebKitFormBoundaryvgqFkBjlcbgD0lQT\r\nContent-Disposition: form-data; name="captcha"\r\n\r\n772ea\r\n------WebKitFormBoundaryvgqFkBjlcbgD0lQT\r\nContent-Disposition: form-data; name="login"\r\n\r\nLogin\r\n------WebKitFormBoundaryvgqFkBjlcbgD0lQT--\r\n' \
'''

URLS = {
    'base': 'https://www.bwssb.gov.in',
    'captcha': '/captcha.php',
    'login': '/login',
    'login_post': '/login.php',
    'logoff': '/CRA/'
}


class BwssbSensor(BaseSensor):
    def download_captcha(self, url):
        logger.info(f"Downloading captcha to {self.captcha_image}")
        self.get(url, verify=False)
        with open(self.captcha_image, 'wb') as ifd:
            ifd.write(self.response.content)

    @retry(CaptchaError, tries=1)
    def solve_captcha(self):
        custom_config = r'--oem 3 --psm 7 -c ' \
            r'tessedit_char_whitelist=0123456789' \
            r'abcdefghijklmnopqrstuvwxyz' \
            r'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        image = Image.open(self.captcha_image).convert('L')
        image = image.filter(ImageFilter.MedianFilter())
        image = image.point(lambda x: 0 if x > 250 else 255)
        #image = image.invert()
        image.save(self.captcha_image.replace('.jpg', '-1.jpg'))
        captcha = pytesseract.image_to_string(image, config=custom_config)
        logger.debug(f"Found Captcha: {captcha}")
        return captcha

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
    sensor = BwssbSensor('finance/bwssb', URLS['base'], headers=headers, creds=True)
#    sensor.get(URLS['login'], verify=False)
#    sensor.get(URLS['captcha'])
#    sensor.download_captcha(URLS['captcha'])
    sensor.solve_captcha()
    done

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
