""" Get BSNL Invoices

"""
import pprint

import logging
from texttable import Texttable

from sensors.basesensor import BaseSensor

logger = logging.getLogger(__name__)

PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://bescom.co.in',
    'login': '/SCP/Myhome.aspx',
    'summary': '/SCP/MyAccount/AccountSummary.aspx?Name=IAccountSummaryView',
    'viewbill': '/SCP/MyAccount/ViewBill.aspx',
}


class BescomSensor(BaseSensor):
    pass


def main(args) -> dict:
    """ Execute the command.
    """
    output = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }
    sensor = BescomSensor('utilities/bescom', headers=headers, base_url=URLS['base'], creds=True)
    sensor.get(URLS['login'])

    view_state = sensor.soup.find(id='__VIEWSTATE')['value']
#    view_state_generator = sensor.soup.find(id='__VIEWSTATEGENERATOR')['value']
    event_validation = sensor.soup.find(id='__EVENTVALIDATION')['value']

    data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': view_state,
        '__EVENTVALIDATION': event_validation,
        'ctl00_ctl00_MasterPageContentPlaceHolder_ToolkitScriptManager2_HiddenField': ';;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:1547e793-5b7e-48fe-8490-03a375b13a33:475a4ef5:effe2a26:1d3ed089:5546a2b:497ef277:a43b07eb:751cdd15:dfad98a5:3cf12cf1',
        'ctl00$ctl00$siteSearch$txtsearch': 'search',
        'ctl00$ctl00$MasterPageContentPlaceHolder$ucLogin$txtUserName': sensor.credentials['username'],
        'ctl00$ctl00$MasterPageContentPlaceHolder$ucLogin$txtPassword': sensor.credentials['password'],
        'ctl00$ctl00$MasterPageContentPlaceHolder$ucLogin$btnLogin': 'Sign In',
    }

    sensor.post(URLS['login'], data=data)

    sensor.get(URLS['viewbill'])
    PP(sensor.soup)
    PP(sensor.response.status_code)
    return outputs


def short(args) -> None:
    table = Texttable()
    output = main(args)
    header = ["BSNL Number", "Name", "Status", "Due in (days)", "Amount Due", "Due Date"]
    table.set_cols_dtype(['t' for x in header])
    status_map = { "SUCCESS": "PAID" }
    table.header(header)
    for row in output:
        name = row["CUSTOMER_NAME"].replace(".", " ").strip()
        table.add_row(
            [str(row["PHONE_NO"]), name, status_map.get(row["STATUS"], "NOT PAID"),
             row["DUE_IN_DAYS"], row["TOTAL_AMOUNT"], row["DUE_DATE"]]
        )
    print(table.draw())
