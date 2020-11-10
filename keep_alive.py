"""
Used for uptime monitoring of bot
"""
from flask import Flask
from threading import Thread

import logging

app = Flask('')


@app.route('/')
def main():
    return 'FrogBot is Up!'


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    # Set log
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    server = Thread(target=run)
    server.start()
