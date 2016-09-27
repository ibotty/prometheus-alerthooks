#!/bin/env python

import logging
import os
import subprocess
import yaml
from http.server import BaseHTTPRequestHandler, HTTPServer
from signal import signal, SIGHUP


CONFIGFILE = os.getenv('ALERTHOOKS_CONFIGFILE', '/etc/prometheus/alerthooks/alerthooks.yml')
PORT = int(os.getenv('ALERTHOOKS_LISTEN_PORT', 8080))
LISTEN_ADDRESS = os.getenv('ALERTHOOKS_LISTEN_ADDRESS', '')
try:
    LOG_LEVEL = getattr(os.getenv('ALERTHOOKS_LOGLEVEL').upper())
except:
    LOG_LEVEL = logging.DEBUG

CONFIG = {}

def load_config(_signum=None, _stack_frame=None):
    global CONFIG
    logging.info('(re)loading config %s', CONFIGFILE)
    with open(CONFIGFILE) as f:
        CONFIG = yaml.load(f)

class AlertHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
        else:
            self.send_response(404)
        self.end_headers()

    def do_POST(self):
        self.path = self.path.rstrip('/')
        try:
            self.process_alert(CONFIG[self.path])
        except KeyError:
            logging.warning('No such path "%s" configured!', self.path)
            self.send_response(404)
        self.end_headers()

    def process_alert(self, alert_config):
        try:
            data = self.rfile.read(int(self.headers['Content-Length']))
            subprocess.run(alert_config['command'], input=data, check=True, shell=True)
            self.send_response(200)
        except KeyError:
            logging.warning('Command for path "%s" undefined!', self.path)
            self.send_response(500)
        except subprocess.CalledProcessError:
            logging.warning('Command "%s" failed!', alert_config['command'])
            self.send_response(500)

def main():
    logging.basicConfig(handlers=[logging.StreamHandler()], level=LOG_LEVEL)
    signal(SIGHUP, load_config)
    load_config()
    HTTPD = HTTPServer((LISTEN_ADDRESS, PORT), AlertHandler)
    logging.info("Listening on %s:%s", LISTEN_ADDRESS, PORT)
    HTTPD.serve_forever()

if __name__ == '__main__':
    main()
