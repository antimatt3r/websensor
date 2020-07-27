import os


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
