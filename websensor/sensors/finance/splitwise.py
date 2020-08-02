""" Implement the vehicle command.

"""
import hashlib
import pprint
import re
from datetime import datetime

from bs4 import BeautifulSoup
import base64
import logging
import json
from texttable import Texttable

from sensors.basesensor import BaseSensor, CaptchaError, LoginError
from utils.utils import convert_currency

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://secure.splitwise.com/',
    'login': '/login',
    'login_post': '/user_session',
    'get_data': '/api/v3.0/get_main_data?no_expenses=1&limit=3',
    'logout': '/logout',
}


class SplitwiseSensor(BaseSensor):
    pass


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
    sensor = SplitwiseSensor('finance/splitwise', URLS['base'], headers=headers)
    sensor.get('login')
#    sensor.dump_html('login-page.html')

    def get_authenticity_token():
        authenticity_token = sensor.soup.find(
            'input', {'name': 'authenticity_token'}).attrs['value']
        return authenticity_token

    authenticity_token = get_authenticity_token()

    logger.info("Logging in now ..")
    data = {
        'authenticity_token': authenticity_token,
        'user_session[email]': sensor.credentials['username'],
        'user_session[password]': sensor.credentials['password'],
        'commit': 'Log+in',
    }
    sensor.post(url=URLS['login_post'], data=data)
#    sensor.dump_html('login-post.html')
    sensor.get(url=URLS['base'])
#    sensor.dump_html('login-inside.html')
    sensor.get(url=URLS['get_data'])
#    sensor.dump_html('dashboard.html')
    data = sensor.response.json()
    for entry in [x for x in data['friends'] if x['balance']]:
        name = entry['first_name'] \
               + (' ' + entry['last_name'] if entry['last_name'] else '')
        for balance in entry['balance']:
            key = f"{name} ({balance['currency_code']})"
            output[key] = {}
            output[key]['name'] = name
            output[key]['currency_code'] = balance['currency_code']
            output[key]['amount'] = balance['amount']
            output[key]['direction'] = \
                'You Owe' if balance['amount'].startswith('-') else 'They Owe'
            output[key]['date'] = datetime.now().strftime('%F')

    logger.info('Logging off ..')
    sensor.post(URLS['logout'],
                data={'authenticity_token': authenticity_token})
    sensor.dump_html('logout.html')
    return output

def short(args) -> None:
    table = Texttable()
    output = main(args)
    date = list(output.values())[0]['date'] \
        if output else datetime.now().strftime('%F')
    header = [f"Splitwise as on {date}", "Currency", "Amount", "Amount (INR)",
              "Who Owes"]
    table.header(header)
    for key, entry in output.items():
        table.add_row([entry['name'],
                       entry['currency_code'],
                       entry['amount'],
                       convert_currency(float(entry['amount']),
                                        entry['currency_code'],
                                        'INR',
                                        date),
                       entry['direction'],
                      ])
    print(table.draw())
#    out = main(args)
