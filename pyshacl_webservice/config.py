# -*- coding: utf-8 -*-
import sys
from os import path

mod = sys.modules[__name__]
mod.CONFIG = CONFIG = {}
CONFIG['APP_HOSTNAME'] = APP_HOSTNAME = '127.0.0.1'
CONFIG['APP_PORT'] = APP_PORT = 8081
CONFIG['DEBUG'] = DEBUG = True
CONFIG['TEMPLATES_DIR'] = TEMPLATES_DIR = path.abspath(path.join(
    path.dirname(__name__), 'templates'))
CONFIG['STATIC_DIR'] = STATIC_DIR = path.abspath(path.join(
    path.dirname(__name__), 'static'))
