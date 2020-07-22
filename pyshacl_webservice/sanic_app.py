# -*- coding: utf-8 -*-
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
import asyncio
from aiohttp import ClientSession
from sanic import Sanic
from sanic.response import HTTPResponse
from sanic.request import Request
from sanic.exceptions import SanicException
from sanic_cors.extension import cors
from sanic_jinja2 import SanicJinja2
from spf import SanicPluginsFramework
from pyshacl_webservice.config import CONFIG
from pyshacl_webservice.util import add_success_callback
from pyshacl_webservice import functions


app = Sanic(__name__)
app.config.LOGO = "PYSHACL WebService - Sanic App"
spf = SanicPluginsFramework(app)
cors, _regd = spf.register_plugin(cors, automatic_options=True)
jinja = SanicJinja2(app)


class InvalidURLException(SanicException):
    pass


app.static('/static', CONFIG['STATIC_DIR'], name='static')

@app.exception(InvalidURLException)
def exception1(request, exception):
    status = exception.status_code
    message = exception.args[0]
    return HTTPResponse("Provided URL is invalid. The target is in the wrong format, "
                        "or does not exist.\r\n{}".format(message),
                        status=status or 406, content_type='text/plain')


@app.route('/about')
def about(request):
    resp = jinja.render('about.html', request)
    resp.headers.add('Access-Control-Allow-Origin', 'http://www.csiro.au/')
    return resp


@app.route('/')
def index(request):
    resp = jinja.render('index.html', request)
    resp.headers.add('Access-Control-Allow-Origin', 'http://www.csiro.au/')
    return resp


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
        data_graph_source = form['dataGraphSource']
        assert len(data_graph_source) > 0, "dataGraphSource not found in form data."
        data_graph_source = data_graph_source[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        shacl_graph_source = form['shaclGraphSource']
        assert len(shacl_graph_source) > 0, "shaclGraphSource not found in form data."
        shacl_graph_source = shacl_graph_source[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        extra_graph_source = form['extraGraphSource']
        assert len(extra_graph_source) > 0, "extraGraphSource not found in form data."
        extra_graph_source = extra_graph_source[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e

    assert data_graph_source in {'text', 'file', 'link'}, "Unsupported Data Graph source."
    assert shacl_graph_source in {'text', 'file', 'link', 'none', None}, "Unsupported SHACL Graph source."
    assert extra_graph_source in {'text', 'file', 'link', 'none', None}, "Unsupported Extra Graph source."

    try:
        data_graph_format = form['dataGraphFormat']
        assert len(data_graph_format) > 0, "dataGraphFormat not found in form data."
        data_graph_format = data_graph_format[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e

    try:
        inference_data_option = form['inferenceDataOption']
        assert len(inference_data_option) > 0, "inferenceDataOption not found in form data."
        inference_data_option = inference_data_option[0]
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        enable_metashacl = form['enableMetashacl']
        enable_metashacl = enable_metashacl[0]
    except (AttributeError, KeyError) as e:
        enable_metashacl = False
    if enable_metashacl and \
                (enable_metashacl == "false" or enable_metashacl == "0"):
        enable_metashacl = False
    if enable_metashacl and \
            (enable_metashacl == "true" or enable_metashacl == "1"):
        enable_metashacl = True
    if data_graph_source == 'file':
        try:
            data_source = request.files['dataSource']
            assert len(data_source) > 0
            data_source = data_source[0].body
        except (AttributeError, KeyError, AssertionError):
            raise FileNotFoundError('Data Source File not found')
        if isinstance(data_source, bytes):
            # Assuming UTF-8 here, this might not always be right.
            data_source = data_source.decode('utf-8')
    else:
        try:
            data_source = form['dataSource']
            assert len(data_source) > 0, 'dataSource not found in the form data.'
            data_source = data_source[0]
        except (AttributeError, KeyError, AssertionError) as e:
            raise e
    if (not shacl_graph_source) or shacl_graph_source == 'none':
        shacl_source = None
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
                shacl_source = request.files['shaclSource']
                assert len(shacl_source) > 0
                shacl_source = shacl_source[0].body
            except (AttributeError, KeyError, AssertionError):
                raise FileNotFoundError('SHACL Source File not found')
            if isinstance(shacl_source, bytes):
                # Assuming UTF-8 here, this might not always be right.
                shacl_source = shacl_source.decode('utf-8')
        else:
            try:
                shacl_source = form['shaclSource']
                assert len(shacl_source) > 0, 'shaclSource not found in the form data.'
                shacl_source = shacl_source[0]
            except (AttributeError, KeyError, AssertionError) as e:
                raise e
    if (not extra_graph_source) or extra_graph_source == 'none':
        extra_source = None
        extra_graph_format = None
    else:
        try:
            extra_graph_format = form['extraGraphFormat']
            assert len(extra_graph_format) > 0, "extraGraphFormat not found in form data."
            extra_graph_format = extra_graph_format[0]
        except (AssertionError, KeyError, AssertionError) as e:
            raise e
        if extra_graph_format == 'file':
            try:
                extra_source = request.files['extraSource']
                assert len(extra_source) > 0
                extra_source = extra_source[0].body
            except (AttributeError, KeyError, AssertionError):
                raise FileNotFoundError('Extra Ontology Source File not found')
            if isinstance(extra_source, bytes):
                # Assuming UTF-8 here, this might not always be right.
                extra_source = extra_source.decode('utf-8')
        else:
            try:
                extra_source = form['extraSource']
                assert len(extra_source) > 0, 'extraSource not found in the form data.'
                extra_source = extra_source[0]
            except (AttributeError, KeyError, AssertionError) as e:
                raise e
    async_futures = set()
    client_session = None
    if data_graph_source == 'link':
        async def data_graph_callback(response):
            nonlocal data_source
            if not (200 <= response.status < 300):
                raise InvalidURLException("Data Graph Url got code {}".format(response.status), 406)
            body = await response.text()
            data_source = body

        assert (data_source[:5].lower() == 'http:' or data_source[:6].lower() == 'https:'),\
            "The Data Graph source link must start with http: or https:"
        client_session = client_session or ClientSession(headers={'Accept': 'text/turtle'})
        get_task = client_session.get(data_source)
        get_future = asyncio.ensure_future(get_task._coro)
        get_future = add_success_callback(get_future, data_graph_callback)
        async_futures.add(get_future)
    if shacl_graph_source == 'link':
        async def shacl_graph_callback(response):
            nonlocal shacl_source
            if not (200 <= response.status < 300):
                raise InvalidURLException("SHACL Url got code {}".format(response.status), 406)
            body = await response.text()
            shacl_source = body

        assert (shacl_source[:5].lower() == 'http:' or shacl_source[:6].lower() == 'https:'),\
            "The SHACL Graph source link must start with http: or https:"
        client_session = client_session or ClientSession(headers={'Accept': 'text/turtle'})
        get_task = client_session.get(shacl_source)
        get_future = asyncio.ensure_future(get_task._coro)
        get_future = add_success_callback(get_future, shacl_graph_callback)
        async_futures.add(get_future)
    if extra_graph_source == 'link':
        async def extra_graph_callback(response):
            nonlocal extra_source
            if not (200 <= response.status < 300):
                raise InvalidURLException("Extra Graph URL got code {}".format(response.status), 406)
            body = await response.text()
            extra_source = body

        assert (extra_source[:5].lower() == 'http:' or extra_source[:6].lower() == 'https:'),\
            "The Extra Ontology Graph source link must start with http: or https:"
        client_session = client_session or ClientSession(headers={'Accept': 'text/turtle'})
        get_task = client_session.get(extra_source)
        get_future = asyncio.ensure_future(get_task._coro)
        get_future = add_success_callback(get_future, extra_graph_callback)
        async_futures.add(get_future)
    if len(async_futures) > 0:
        _done = await asyncio.gather(*async_futures, return_exceptions=False)
        print(_done)
    try:
        r = functions.run_validate(data_source, data_graph_format, shacl_source,
                                   shacl_graph_format,
                                   ont_graph=extra_source,
                                   ont_graph_format=extra_graph_format,
                                   inference=inference_data_option,
                                   enable_metashacl=enable_metashacl)
    except Exception:
        raise
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




