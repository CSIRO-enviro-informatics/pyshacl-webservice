# encoding: utf-8
from pyshacl_webservice.util import version
import logging
logging.basicConfig(level=logging.INFO)
try:
    import sanic
    v = version.parse(sanic.__version__)
    r_v = version.parse('0.8.1')
    assert (v >= r_v), "Requires sanic >= {}".format(r_v)
except (ImportError, AssertionError) as e:
    logging.error(str(e))
    raise RuntimeError(
        "Please install `sanic` to use Sanic app functionality.")
from os import path
from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.request import Request
from sanic_cors.extension import cors
from spf import SanicPluginsFramework
from pyshacl_webservice.config import CONFIG


app = Sanic(__name__)
app.config.LOGO = "PYSHACL WebService - Sanic App"
spf = SanicPluginsFramework(app)
cors, _regd = spf.register_plugin(cors, automatic_options=True)


_index_html_file = path.join(CONFIG['TEMPLATES_DIR'], 'layout.html')
app.static('/', _index_html_file, name='index')

app.static('/static', CONFIG['STATIC_DIR'], name='static')


@app.route('/validate', methods={'POST'})
def validate(request):
    """
    This is the POST endpoint for the VALIDATE
    :param request:
    :type request: Request
    :return: HTTPResponse
    """
    try:
        form = request.form
        assert form
    except Exception as e:
        raise e



if __name__ == "__main__":
    logging.warning("Running the Sanic app as an executable.\n"
                    "This is fine for debugging and testing, however "
                    "this is not the recommended way to run the Sanic app.")
    app.run(host=CONFIG['APP_HOSTNAME'], port=CONFIG['APP_PORT'],
            debug=CONFIG['DEBUG'])




