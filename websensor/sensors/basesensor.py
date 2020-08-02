import base64
import logging
import os
import pprint
import json
import re
from os.path import basename, join

import requests
from bs4 import BeautifulSoup
from pytesseract import pytesseract
from retry import retry

from utils.config import Config

try:
    from PIL import Image
except ImportError:
    import Image

logger = logging.getLogger(__name__)
PP = pprint.PrettyPrinter(indent=4).pprint


class NoCredsError(Exception):
    pass


class CaptchaError(Exception):
    pass


class LoginError(Exception):
    pass


class BaseSensor(object):
    def __init__(self, name, base_url, parser='html.parser', headers=None, creds=True):
        self.name = name
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if headers:
            self.session.headers = headers
        self.response = None
        self.soup = None
        self.parser = parser

        self.config = Config()
        self.tmpdir = self.config.config['tmpdir']
        if self.tmpdir.split('/')[-1] != 'websensor':
            self.tmpdir = join(self.tmpdir, 'websensor')
        os.makedirs(self.tmpdir, exist_ok=True)
        self.inputs = self.read_from_config('inputs', raise_=False)
        self.credentials = self.read_from_config('secrets', raise_=creds)
        self.captcha_image = join(self.tmpdir,
                                  self.get_qualified_name("captcha.jpg"))

    def read_from_config(self, type_, raise_=True):
        data = self.config.config[type_]
        if isinstance(data, str):
            with open(data) as jfd:
                data = json.load(jfd)
        path = []
        for component in self.name.split('/'):
            path.append(component)
            if component in data:
                data = data[component]
            else:
                if raise_:
                    raise Exception(f"No section {'/'.join(path)} in {self.config}")
                else:
                    return None
        return data

    def encode_password(self, password):
        pass

    def request(self, method, url, **kwargs):
        if not url.startswith('http'):
            url = f'{self.base_url}/{url.lstrip("/")}'
        self.response = self.session.get(url, **kwargs)
        self.soup = BeautifulSoup(self.response.text, self.parser)
        self.response.raise_for_status()
        return self.reponse

    def get(self, url, **kwargs):
        if not url.startswith('http'):
            url = f'{self.base_url}/{url.lstrip("/")}'
        self.response = self.session.get(url, **kwargs)
        self.soup = BeautifulSoup(self.response.text, self.parser)
        self.response.raise_for_status()

    def post(self, url, **kwargs):
#        return self.request('post', url, **kwargs)
        if not url.startswith('http'):
            url = f'{self.base_url}/{url.lstrip("/")}'
        logger.debug(f"POSTing to {url} ..")
        self.response = self.session.post(url, **kwargs)
        logger.debug("Creating soup ..")
        self.soup = BeautifulSoup(self.response.text, self.parser)
        self.response.raise_for_status()

    def download_captcha(self, url):
        logger.info(f"Downloading captcha to {self.captcha_image}")
#        self.get(url)
#        image = self.soup.find(id='captcha_id')['src'].split('base64,')[1]
#        with open(self.captcha_image, 'wb') as ifd:
#            ifd.write(base64.b64decode(image))

    def process_captcha(self, captcha):
        logger.info(f"Processing captcha {captcha}")
#        captcha = re.sub(r'[^0-9]+$', '', captcha)
#        captcha = re.sub(r'^[^0-9]+', '', captcha)
#        match = re.match(r'^\d+\s*[/*+-]\d+$', captcha)
#        if not match:
#            raise CaptchaError(f"Unable to solve captcha: {captcha}")
#        result = eval(captcha)
#        return result

    @retry(CaptchaError, tries=3)
    def solve_captcha(self, url):
        self.download_captcha(url)

        custom_config = r'--oem 3 --psm 6 -c ' \
                        r'tessedit_char_whitelist=0123456789+=-'
        captcha = pytesseract.image_to_string(Image.open(self.captcha_image),
                                              config=custom_config)
        logger.debug(f"Found Captcha: {captcha}")
        result = self.process_captcha(captcha)
        return result

    def get_qualified_name(self, filename):
        q_name = f"{self.name.replace('/', '-')}-{basename(filename)}"
        if not filename.startswith('/'):
            filename = join(self.tmpdir, q_name)
        else:
            filename = q_name
        return filename

    def dump_html(self, filename):
        filename = self.get_qualified_name(filename)
        with open(filename, 'w') as hfd:
            logger.debug("Writing %s", filename)
            hfd.write(self.response.text)

    def read_html(self, filename):
        filename = self.get_qualified_name(filename)
        with open(filename) as hfd:
            logger.debug("Reading %s", filename)
            html = hfd.read()
        self.soup = BeautifulSoup(html, self.parser)
