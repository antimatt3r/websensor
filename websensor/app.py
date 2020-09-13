from os.path import dirname, abspath

from flask import Flask, jsonify, make_response
import sys
sys.path.append(dirname(abspath(__file__)))
import importlib

import logging
logger = logging.getLogger()

app = Flask(__name__)


@app.route('/')
def home():
    return 'Hit /sensor/SENSOR'
    return jsonify(make_response(
       {'success': 'Hit /sensor/SENSOR'}))


@app.route('/sensor/<path:sensor>')
def sensor(sensor):
    sensor = sensor.replace("/", ".")
    if sensor.split('/') == 'finance':
        return make_response(
            jsonify({'error': 'Finance sensor is not supported'}),
            403
        )
    logger.critical(f"sensor = {sensor}")
    module = importlib.import_module(f'sensors.{sensor}')
    return jsonify(getattr(module, 'main')(args=None))


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, use_reloader=False)
