import os
import re
from collections import OrderedDict


def drop_to_shell():
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
    code.interact(local=dict(globals(), **locals()))

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
