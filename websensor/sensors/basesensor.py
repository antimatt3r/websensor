import base64
import logging
import os
import pprint
import json
import re
from os.path import dirname, abspath, isdir

import requests
from bs4 import BeautifulSoup
from pytesseract import pytesseract
from retry import retry

from utils.config import Config
from jsonpath_ng import parse

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
        self.captcha_image = os.environ['HOME'] + '/tmp/pfimg.jpg'

        self.config = Config()
        self.inputs = self.read_from_config('inputs', raise_=False)
        self.credentials = self.read_from_config('secrets', raise_=creds)

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
        logger.debug(f"POSTing to {url} with data: {kwargs['data']} ..")
        self.response = self.session.post(url, **kwargs)
        logger.debug("Creating soup ..")
        self.soup = BeautifulSoup(self.response.text, self.parser)
        self.response.raise_for_status()

    def download_captcha(self, url):
        logger.info(f"Downloading captcha to {self.captcha_image}")
        self.get(url)
        image = self.soup.find(id='captcha_id')['src'].split('base64,')[1]
        with open(self.captcha_image, 'wb') as ifd:
            ifd.write(base64.b64decode(image))

    def process_captcha(self, captcha):
        captcha = re.sub(r'[^0-9]+$', '', captcha)
        captcha = re.sub(r'^[^0-9]+', '', captcha)
        match = re.match(r'^\d+\s*[/*+-]\d+$', captcha)
        if not match:
            raise CaptchaError(f"Unable to solve captcha: {captcha}")
        result = eval(captcha)
        return result

    @retry(CaptchaError, tries=3)
    def solve_captcha(self, url):
        self.download_captcha(url)

        custom_config = r'--oem 3 --psm 6'
        captcha = pytesseract.image_to_string(Image.open(self.captcha_image), config=custom_config)
        logger.debug(f"Found Captcha: {captcha}")
        result = self.process_captcha(captcha)
        return result

