#!/bin/env python

import os
import subprocess
import yaml
from http.server import BaseHTTPRequestHandler, HTTPServer
from signal import signal, SIGHUP


CONFIGFILE = os.getenv('ALERTHOOKS_CONFIGFILE', '/etc/prometheus/alerthooks/alerthooks.yml')
PORT = int(os.getenv('ALERTHOOKS_LISTEN_PORT', 8080))
LISTEN_ADDRESS = os.getenv('ALERTHOOKS_LISTEN_ADDRESS', '')

CONFIG = {}

def load_config(_signum=None, _stack_frame=None):
    global CONFIG
    print('(re)loading config %s' % CONFIGFILE)
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
            print('No such path "%s" configured!' % self.path)
            self.send_response(404)
        self.end_headers()

    def process_alert(self, alert_config):
        try:
            data = self.rfile.read(int(self.headers['Content-Length']))
            subprocess.run(alert_config['command'], input=data, check=True, shell=True)
            self.send_response(200)
        except KeyError:
            print('Command for path "%s" undefined!' % self.path)
            self.send_response(500)
        except subprocess.CalledProcessError:
            print('Command "%s" failed!' % alert_config['command'])
            self.send_response(500)

if __name__ == '__main__':
    signal(SIGHUP, load_config)
    load_config()
    HTTPD = HTTPServer((LISTEN_ADDRESS, PORT), AlertHandler)
    HTTPD.serve_forever()
