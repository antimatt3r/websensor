import json
import logging
import os
import shutil
import tempfile

logger = logging.getLogger(__name__)
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
        self.tmpdir_created = False
        self.tmpdir = self.create_temp_dir()

    def create_temp_dir(self):
        # You can define where you can to create a temporary files. May be
        # useful for debugging
        dir_ = self.config.get("tmpdir")
        if dir_ and os.path.isdir(dir_):
            return dir_
        elif dir_:
            raise Exception(f"Invalid tempdir provided in config: {dir_}")
        else:
            logger.debug(f"Created temporary directory {tempdir}")
            tempdir = tempfile.mkdtemp()
            self.tmpdir_created = True
            return tempdir

    def __del__(self):
        if self.tmpdir_created:
            logger.debug(f"Cleaning temporary directory: {self.tmpdir}")
            shutil.rmtree(self.tmpdir)
