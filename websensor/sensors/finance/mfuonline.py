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
    'base': 'https://www.mfuonline.com',
    'login': '/MfUtilityLogin.do',
    'investment': '/InvHoldingDetailsAction.do?',
}

class MfuOnlineSensor(BaseSensor):
    pass


'''
curl 'https://www.mfuonline.com/MfUtilityLogin.do'
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0'
-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
--compressed
-H 'Content-Type: application/x-www-form-urlencoded'
-H 'Cookie: JSESSIONID=B166C096B547CEB774390D427BF84B9D'
--data-raw 'localeID=&loginid=USER&password=PASS&lang1=success'

curl 'https://www.mfuonline.com/InvHoldingDetailsAction.do?'--compressed
-H 'Cookie: JSESSIONID=7765B68906D4EFD1D0695B6D6CCBA362'
--data-raw 'canID=CANID&respType=detail&verType=ver2&zeroHoldingFlag=Y&holdingforAllFlag=N&canHolderType=F&accCategory=I'
'''

def main(args) -> dict:
    """ Execute the command.

    :param name: name to use in greeting
    """
    output = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    sensor = MfuOnlineSensor('finance/mfuonline', URLS['base'], headers=headers)

    login_data = {
        'localeID': '',
        'loginid': sensor.credentials['username'],
        'password': sensor.credentials['password'],
        'lang1': 'success',
    }

    investment_data = {
        'canID': sensor.credentials['canid'],
        'respType': 'detail',
        'verType': 'ver2',
        'zeroHoldingFlag': 'N',
        'holdingforAllFlag': 'N',
        'canHolderType': 'F',
        'accCategory': 'I',
    }

    logger.info("Logging in now ..")
    sensor.get(URLS['base'])
    sensor.post(URLS['login'], data=login_data)
#    sensor.dump_html('login.html')
    sensor.post(URLS['investment'], data=investment_data)
#    sensor.dump_html('investment.html')
#    sensor.read_html('investment.html')

    categorydata = sensor.soup.find('div', id='catHoldDash')
    funds = categorydata.find_all('li', {'class': 'list-group-item pleft5'})

    def clean_text(text):
        return re.sub(r'\s+', ' ', text).strip()

    def get_fund_details(soup):
        details = {}
        fund_details = soup.find('div', {'class': 'col-md-4 col-lg-4'})
        fund_details_re = re.compile(r'(?P<name>.*)\s+Current Value is based'
                                     r' on NAV\s*:\s*(?P<nav>[0-9\.]+) as'
                                     r' on NAV Date: (?P<nav_date>.*)')
        match = fund_details_re.search(clean_text(fund_details.text))
        details.update(match.groupdict())

        folio_details = soup.find('div', {'class': 'col-md-2 col-lg-2'})
        details.update(
            {'folio': clean_text(folio_details.text).replace(' /', '/')})

        unit_details = soup.find(
            'div', {'class': 'col-md-2 col-lg-2 pright5 number'})
        details.update(
            {'units': clean_text(unit_details.text).replace(' (U)', '')})

        value_details = soup.find(
            'div', {'class': 'col-md-4 col-lg-4 pleft5 pright5 number'})
        details.update(
            {'value': clean_text(value_details.text).replace(',', '')})
        return details

    for fund in funds:
        details = get_fund_details(fund)
        output[details['name']] = details

    return output

def short(args) -> None:
    table = Texttable()
    output = main(args)
    columns = ['name', 'folio', 'nav', 'units', 'value']
    nav_date = list(output.values())[0]['nav_date']
    header = [f"MF as on {nav_date}", "Folio", "Nav", "Units", "Value"]
    table.header(header)
    table.set_cols_dtype(['t' for x in columns])
    for mf in sorted(output):
        row = [output[mf][x] for x in columns]
        table.add_row(row)
    print(table.draw())
#    out = main(args)
