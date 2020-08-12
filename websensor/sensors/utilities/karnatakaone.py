""" Get BSNL Invoices

"""
import pprint

import logging
from texttable import Texttable

from sensors.basesensor import BaseSensor

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://www.karnatakaone.gov.in/',
    'home': '/Home',
}

class BsnlSensor(BaseSensor):
    def encode_password(self, password):
        seed = self.soup.find('input', {'name': 'Seed'}).attrs['value']
        PP("------------------------")
        PP(seed)
    pass


def main(args) -> dict:
    """ Execute the command.
    """
    output = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Content-Type': 'text/html; charset=utf-8',
    }
    sensor = BsnlSensor('utilities/karnatakaone', headers=headers, base_url=URLS['base'], creds=True)
    sensor.get(URLS['home'])
    sensor.dump_html('home.html')
    PP(sensor.soup.find('input', {'name': '__RequestVerificationToken'}).attrs['value'])
    aklsdjf
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

