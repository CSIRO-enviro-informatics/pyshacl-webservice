# -*- coding: latin-1 -*-
import sys
assert sys.version[0] == "3", "Please use python3.6+"
try:
    from pyshacl_webservice.sanic_app import app as sanic_app
except (ImportError, RuntimeError):
    sanic_app = None

try:
    from pyshacl_webservice.flask_app import app as flask_app
except (ImportError, RuntimeError):
    flask_app = None

# version compliant with https://www.python.org/dev/peps/pep-0440/
__version__ = '0.1.0a5.dev20200722'

__all__ = ['flask_app', 'sanic_app', '__version__']
