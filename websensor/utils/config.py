import json
import os
import tempfile

def get_config():
    websensorrc = os.environ.get('WEBSENSORRC',
                                 os.path.expanduser('~/.websensorrc'))
    try:
        with open(websensorrc) as rcfd:
            config = json.load(rcfd)
        return config
    except IOError:
        print("ioerror")


def get_secrets(config):
    secrets_file = config['secrets']
    with open(secrets_file) as sfd:
        secrets = json.load(sfd)
    return secrets


class Config(object):
    def __init__(self):
        self.config = get_config()
        self.secrets = get_secrets(self.config)
        self._tmpdir = self.create_temp_dir()
        self.tmpdir = self._tmpdir.name

    def create_temp_dir(self):
        # You can define where you can to create a temporary files. May be
        # useful for debugging
        dir_ = self.config.get("tmpdir")
        tempdir = tempfile.TemporaryDirectory(dir=dir_)
        return tempdir

    def __del__(self):
        self._tmpdir.cleanup()
