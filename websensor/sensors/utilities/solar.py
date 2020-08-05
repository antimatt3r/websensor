""" Implement the vehicle command.

"""
import pprint
import re

import logging
import datetime

from texttable import Texttable

from sensors.basesensor import BaseSensor
import pygoodwe

logger = logging.getLogger()
PP = pprint.PrettyPrinter(indent=4).pprint

URLS = {
    'base': 'https://www.semsportal.com/',
    'login': '/home/login',
    'login_post': '/Home/Login',
    'dashboard': '/PowerStation/PowerStatusSnMin/{station_id}'
}


class SolarSensor(BaseSensor):
    pass


def main(args) -> dict:
    """ Execute the command.

    :param name: name to use in greeting
    """
    output = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    sensor = SolarSensor('utilities/solar', headers=headers, base_url=URLS['base'], creds=True)

#    data = {
#        'account': sensor.credentials['username'],
#        'pwd': sensor.credentials['password']
#    }
#    sensor.get(URLS['login'])
#    sensor.post(URLS['login_post'], data=data)
#    station_id = sensor.response.json()['data']['redirect'].split('/')[-1]
#
#    sensor.get(URLS['dashboard'].format(station_id=station_id))
#    sensor.dump_html('dash.html')
#
#    post_data = {
#        "api": "v1/PowerStation/GetMonitorDetailByPowerstationId",
#        "param": {"powerStationId": sensor.credentials['station_id']}
#    }
#    sensor.post('/GopsApi/Post?s=v1/PowerStation/GetMonitorDetailByPowerstationId',
#                data=post_data)
#    PP(sensor.response.text)
#    sensor.dump_html('monitor.html')

    api = pygoodwe.API(sensor.credentials['station_id'],
                       sensor.credentials['username'],
                       sensor.credentials['password'])

    def get_statistics(numbers, prefix):
        nonzero_numbers = numbers.copy()
        while nonzero_numbers[-1] == 0:
            nonzero_numbers.pop()
        print(nonzero_numbers)

        def average(list_):
            return sum(list_)/len(list_) if list_ else 0

        funcs = {
            'total': sum, 'min': min, 'max': max, 'average': average
        }
        return {
            prefix + "_" + param: funcs[param](nonzero_numbers)
            for param in funcs
        }

    def get_user_defined(start, end, prefix):
        PP((start, end))
        if isinstance(start, datetime.datetime):
            start = start.strftime('%m/%d/%Y')
        if isinstance(end, datetime.datetime):
            end = end.strftime('%m/%d/%Y')
        payload = {
            "ids":api.system_id,
            "sns":"",
            "range":4,"type":2,
            "start":start,"end":end
        }
        out = api.call('v1/Statistics/GetStatisticsCharts_Sn', payload)
        return get_statistics([x['y'] for x in out[0]['yield']], prefix)

    def get_monthly_stats(date, prefix):
        if isinstance(date, datetime.datetime):
            date = date.strftime('%m/%d/%Y')
        payload = {
            "ids": api.system_id,
            "range": 1, "type": 3,
            "start": date, "end": "",
            "pageIndex": 1, "pageSize": 31
        }
        out = api.call('v1/Statistics/GetStatisticsData', payload)
        numbers = [x['generation'] for x in out['rows']]
        return get_statistics(numbers, prefix)
    #    output.update(get_monthly_stats(first_of_last_month, 'last_month'))

    today = datetime.date.today()
    start_of_last_week = today - datetime.timedelta(days=7)
    end_of_last_week = today - datetime.timedelta(days=1)
    first_of_this_month = today.replace(day=1)
    end_of_last_month = first_of_this_month - datetime.timedelta(days=1)
    first_of_last_month = end_of_last_month.replace(day=1)

    output.update(get_user_defined(start_of_last_week,
                                   end_of_last_week,
                                   "last_week"))
    output.update(get_user_defined(first_of_last_month,
                                   end_of_last_month,
                                   'last_month'))
    output.update(get_user_defined(first_of_this_month, today, 'this_month'))

    output['today'] = api.data['kpi']['power']
    output['total'] = api.data['kpi']['total_power']
    output['date'] = today.strftime('%Y-%m-%d')
    output['plant'] = api.system_id
    return output

def short(args) -> None:
    table = Texttable()
    output = main(args)
    header = [f"Generated units {output['date']}", "Today", "Last Week",
              "This Month", "Last Month", "Total"]
    table.header(header)
    table.add_row([
        output['plant'], output['today'], output['last_week_total'],
        output['this_month_total'], output['last_month_total'],
        output['total']
    ])
    print(table.draw())
#    out = main(args)
