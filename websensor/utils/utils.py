import inspect
import os
import re
import code
from collections import OrderedDict

import requests
import logging

logger = logging.getLogger()


def drop_to_shell():
    vars = {}
    vars.update(globals())
    try:
        frame = inspect.currentframe()
        locals = frame.f_back.f_locals
        vars.update(locals)
    except Exception:
        pass
    try:
        import readline
        import rlcompleter
        historyPath = os.path.expanduser("~/.pyhistory")
        if os.path.exists(historyPath):
            readline.read_history_file(historyPath)
        readline.parse_and_bind('tab: complete')
        readline.set_completer(rlcompleter.Completer(vars).complete)
    except Exception:
        pass
    code.interact(local=vars)


def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def list_of_lists_to_dict(data, key):
    headers = data.pop(0)
    try:
        index_key = headers.index(key)
    except ValueError:
        raise Exception(f"Given Key is not a part of the headers: {headers}")
    dict_ = OrderedDict()
    for row in data:
        dict_.update({row[index_key]: dict(zip(headers, row))})
    return dict_


def convert_currency(amount, from_, to, date='latest'):
    rates = requests.get(f'https://api.exchangeratesapi.io/{date}').json()
    if from_ == to:
        out = amount
    elif from_ == rates['base']:
        out = amount * rates['rates'][to]
    elif to == rates['base']:
        out = amount / rates['rates'][from_]
    else:
        out = amount * rates['rates'][to] / rates['rates'][from_]
    logger.info(f"{amount} {from_} = {out} {to}")
    return out
