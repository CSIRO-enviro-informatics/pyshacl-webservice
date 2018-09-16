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
import asyncio
from aiohttp import ClientSession
from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.request import Request
from sanic.exceptions import SanicException
from sanic_cors.extension import cors
from spf import SanicPluginsFramework
from pyshacl_webservice.config import CONFIG
from pyshacl_webservice.util import add_success_callback
from pyshacl_webservice import functions


app = Sanic(__name__)
app.config.LOGO = "PYSHACL WebService - Sanic App"
spf = SanicPluginsFramework(app)
cors, _regd = spf.register_plugin(cors, automatic_options=True)


class InvalidURLException(SanicException):
    pass


_index_html_file = path.join(CONFIG['STATIC_DIR'], 'index.html')
app.static('/', _index_html_file, name='index')

app.static('/static', CONFIG['STATIC_DIR'], name='static')


@app.exception(InvalidURLException)
def exception1(request, exception):
    status = exception.status_code
    message = exception.args[0]
    return HTTPResponse("Provided URL is invalid. The target is in the wrong format, "
                        "or does not exist.\r\n{}".format(message),
                        status=status or 406, content_type='text/plain')


@app.route('/validate', methods={'POST'})
async def validate(request):
    """
    This is the POST endpoint for the VALIDATE
    :param request:
    :type request: Request
    :return: HTTPResponse
    """
    form = request.form
    try:
        target_graph_source = form['targetGraphSource']
        assert len(target_graph_source) > 0, "targetGraphSource not found in form data."
        target_graph_source = target_graph_source[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        shacl_graph_source = form['shaclGraphSource']
        assert len(shacl_graph_source) > 0, "shaclGraphSource not found in form data."
        shacl_graph_source = shacl_graph_source[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e

    assert target_graph_source in {'text', 'file', 'link'}, "Unsupported Target Graph source."
    assert shacl_graph_source in {'text', 'file', 'link', 'none', None}, "Unsupported SHACL Graph source."

    try:
        target_graph_format = form['targetGraphFormat']
        assert len(target_graph_format) > 0, "targetGraphFormat not found in form data."
        target_graph_format = target_graph_format[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e

    try:
        inference_target_option = form['inferenceTargetOption']
        assert len(inference_target_option) > 0, "inferenceTargetOption not found in form data."
        inference_target_option = inference_target_option[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    if target_graph_source == 'file':
        try:
            target_data = request.files['targetData']
            assert len(target_data) > 0
            target_data = target_data[0].body
        except (AttributeError, KeyError, AssertionError):
            raise FileNotFoundError('Target Data File not found')
        if isinstance(target_data, bytes):
            # Assuming UTF-8 here, this might not always be right.
            target_data = target_data.decode('utf-8')
    else:
        try:
            target_data = form['targetData']
            assert len(target_data) > 0, 'targetData not found in the form data.'
            target_data = target_data[0]
        except (AttributeError, KeyError, AssertionError) as e:
            raise e
    if (not shacl_graph_source) or shacl_graph_source == 'none':
        shacl_data = None
        shacl_graph_format = None
    else:
        try:
            shacl_graph_format = form['shaclGraphFormat']
            assert len(shacl_graph_format) > 0, "shaclGraphFormat not found in form data."
            shacl_graph_format = shacl_graph_format[0]
        except (AssertionError, KeyError, AssertionError) as e:
            raise e
        if shacl_graph_source == 'file':
            try:
                shacl_data = request.files['shaclData']
                assert len(shacl_data) > 0
                shacl_data = shacl_data[0].body
            except (AttributeError, KeyError, AssertionError):
                raise FileNotFoundError('SHACL Data File not found')
            if isinstance(shacl_data, bytes):
                # Assuming UTF-8 here, this might not always be right.
                shacl_data = shacl_data.decode('utf-8')
        else:
            try:
                shacl_data = form['shaclData']
                assert len(shacl_data) > 0, 'shaclData not found in the form data.'
                shacl_data = shacl_data[0]
            except (AttributeError, KeyError, AssertionError) as e:
                raise e
    async_futures = set()
    client_session = None
    if target_graph_source == 'link':
        async def target_graph_callback(response):
            nonlocal target_data
            if not (200 <= response.status < 300):
                raise InvalidURLException("Target Url got code {}".format(response.status), 406)
            body = await response.text()
            target_data = body

        assert (target_data[:5].lower() == 'http:' or target_data[:6].lower() == 'https:'),\
            "The Target Graph source link must start with http: or https:"
        client_session = client_session or ClientSession(headers={'Accept': 'text/turtle'})
        get_task = client_session.get(target_data)
        get_future = asyncio.ensure_future(get_task._coro)
        get_future = add_success_callback(get_future, target_graph_callback)
        async_futures.add(get_future)
    if shacl_graph_source == 'link':
        async def shacl_graph_callback(response):
            nonlocal shacl_data
            if not (200 <= response.status < 300):
                raise InvalidURLException("SHACL Url got code {}".format(response.status), 406)
            body = await response.text()
            shacl_data = body

        assert (shacl_data[:5].lower() == 'http:' or shacl_data[:6].lower() == 'https:'),\
            "The SHACL Graph source link must start with http: or https:"
        client_session = client_session or ClientSession(headers={'Accept': 'text/turtle'})
        get_task = client_session.get(shacl_data)
        get_future = asyncio.ensure_future(get_task._coro)
        get_future = add_success_callback(get_future, shacl_graph_callback)
        async_futures.add(get_future)
    if len(async_futures) > 0:
        _done = await asyncio.gather(*async_futures, return_exceptions=False)
        print(_done)
    try:
        r = functions.run_validate(target_data, target_graph_format, shacl_data,
                                   shacl_graph_format, inference_target_option)
    except Exception as e:
        raise e
    conforms, report = r
    return HTTPResponse(None, status=200,
                        headers={'Content-Type': 'application/ld+json'},
                        body_bytes=report)


if __name__ == "__main__":
    logging.warning("Running the Sanic app as an executable.\n"
                    "This is fine for debugging and testing, however "
                    "this is not the recommended way to run the Sanic app.")
    app.run(host=CONFIG['APP_HOSTNAME'], port=CONFIG['APP_PORT'],
            debug=CONFIG['DEBUG'], auto_reload=False)




