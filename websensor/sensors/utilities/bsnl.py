""" Get BSNL Invoices

"""
import pprint

import logging
from texttable import Texttable

from sensors.basesensor import BaseSensor

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://portal.bsnl.in',
    'authorize': '/myportal/authorize.do',
    'login': '/myportal/validateLogin.do',
    'initial': '/myportal/Login.jsp',
    'invoices': '/myportal/getinvoices.do',
}

class BsnlSensor(BaseSensor):
    pass


def main(args) -> dict:
    """ Execute the command.
    """
    output = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://portal.bsnl.in',
        'Referer': 'https://portal.bsnl.in/myportal/authorize.do',
    }
    sensor = BsnlSensor('utilities/bsnl', headers=headers, base_url=URLS['base'], creds=True)
    sensor.get(URLS['authorize'])
    sensor.post(URLS['initial'])

    data = {
        'userName': sensor.credentials['username'],
        'passWord': sensor.credentials['password']
    }
    #sensor.post(URLS['login'] + '?' + urllib.parse.urlencode(data))
    sensor.post(URLS['login'], data=data)
    sensor.post(URLS['invoices'], data={'vertical': 'CM'})
    outputs = sensor.response.json()['ROWSET']['ROW']

    return outputs

def short(args) -> None:
    table = Texttable()
    output = main(args)
    header = ["BSNL Number", "Name", "Status", "Due in (days)", "Amount Due", "Due Date"]
    table.set_cols_dtype(['t' for x in header])
    def get_status(entry):
        return "NOT PAID" \
            if entry['BILL_STATUS'] == 'R' \
               and entry['TOTAL_AMOUNT'] > 0 \
            else "PAID"
    table.header(header)
    for row in output:
        name = row["CUSTOMER_NAME"].replace(".", " ").strip()
        table.add_row(
            [str(row["PHONE_NO"]), name, get_status(row),
             row["DUE_IN_DAYS"], row["TOTAL_AMOUNT"], row["DUE_DATE"]]
        )
    print(table.draw())
