# -*- coding: utf-8 -*-
from pyshacl_webservice.util import version
import logging
logging.basicConfig(level=logging.INFO)
try:
    import flask
    v = version.parse(flask.__version__)
    r_v = version.parse('0.12.2')
    assert (v >= r_v), "Requires flask >= {}".format(r_v)
except (ImportError, AssertionError) as e:
    logging.error(str(e))
    raise RuntimeError(
        "Please install `flask` to use Flask app functionality.")
from flask import Flask, Response, request, render_template
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from requests import Session
from requests.exceptions import ConnectionError, ConnectTimeout
from pyshacl_webservice.config import CONFIG
from pyshacl_webservice import functions


app = Flask(__name__, static_folder=CONFIG['STATIC_DIR'])
cors = CORS(app)


class InvalidURLException(HTTPException):
    pass


@app.errorhandler(InvalidURLException)
def exception1(exception):
    status = exception.code
    message = exception.get_description()
    return Response("Provided URL is invalid. The target is in the wrong format, "
                    "or does not exist.\r\n{}".format(message),
                    status=status or 406, content_type='text/plain')


@app.route('/')
def index():
    return render_template(
        'index.html',
        headers={'Access-Control-Allow-Origin': 'http://www.csiro.au/'}
    )


@app.route('/about',)
def about():
    return render_template(
        'about.html',
        headers={'Access-Control-Allow-Origin': 'http://www.csiro.au/'}
    )


@app.route('/validate', methods={'POST'})
def validate():
    """
    This is the POST endpoint for the VALIDATE
    :param request:
    :type request: Request
    :return: HTTPResponse
    """
    form = request.form
    try:
        data_graph_source = form['dataGraphSource']
        assert data_graph_source, "dataGraphSource not found in form data."
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        shacl_graph_source = form['shaclGraphSource']
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        extra_graph_source = form['extraGraphSource']
    except (AttributeError, KeyError, AssertionError) as e:
        raise e


    assert data_graph_source in {'text', 'file', 'link'}, "Unsupported Data Graph source."
    assert shacl_graph_source in {'text', 'file', 'link', 'none', None}, "Unsupported SHACL Graph source."
    assert extra_graph_source in {'text', 'file', 'link', 'none', None}, "Unsupported Extra Graph source."
    try:
        data_graph_format = form['dataGraphFormat']
        assert data_graph_format, "dataGraphFormat not found in form data."
    except (AttributeError, KeyError, AssertionError) as e:
        raise e

    try:
        inference_data_option = form['inferenceDataOption']
        assert inference_data_option, "inferenceDataOption not found in form data."
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        enable_metashacl = form['enableMetashacl']
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
            assert data_source
            data_source = data_source.read()
        except (AttributeError, KeyError, AssertionError):
            raise FileNotFoundError('Data Source File not found')
        if isinstance(data_source, bytes):
            # Assuming UTF-8 here, this might not always be right.
            data_source = data_source.decode('utf-8')
    else:
        try:
            data_source = form['dataSource']
            assert data_source, 'dataSource not found in the form data.'
        except (AttributeError, KeyError, AssertionError) as e:
            raise e
    if (not shacl_graph_source) or shacl_graph_source == 'none':
        shacl_source = None
        shacl_graph_format = None
    else:
        try:
            shacl_graph_format = form['shaclGraphFormat']
            assert shacl_graph_format, "shaclGraphFormat not found in form data."
        except (AssertionError, KeyError, AssertionError) as e:
            raise e
        if shacl_graph_source == 'file':
            try:
                shacl_source = request.files['shaclSource']
                assert shacl_source
                shacl_source = shacl_source.read()
            except (AttributeError, KeyError, AssertionError):
                raise FileNotFoundError('SHACL Source File not found')
            if isinstance(shacl_source, bytes):
                # Assuming UTF-8 here, this might not always be right.
                shacl_source = shacl_source.decode('utf-8')
        else:
            try:
                shacl_source = form['shaclSource']
                assert shacl_source, 'shaclSource not found in the form data.'
            except (AttributeError, KeyError, AssertionError) as e:
                raise e
    if (not extra_graph_source) or extra_graph_source == 'none':
        extra_source = None
        extra_graph_format = None
    else:
        try:
            extra_graph_format = form['extraGraphFormat']
            assert extra_graph_format, "extraGraphFormat not found in form data."
        except (AssertionError, KeyError, AssertionError) as e:
            raise e
        if extra_graph_format == 'file':
            try:
                extra_source = request.files['extraSource']
                assert extra_source
                extra_source = extra_source.read()
            except (AttributeError, KeyError, AssertionError):
                raise FileNotFoundError('Extra Ontology Source File not found')
            if isinstance(extra_source, bytes):
                # Assuming UTF-8 here, this might not always be right.
                extra_source = extra_source.decode('utf-8')
        else:
            try:
                extra_source = form['extraSource']
                assert extra_source, 'extraSource not found in the form data.'
            except (AttributeError, KeyError, AssertionError) as e:
                raise e
    client_session = None
    if data_graph_source == 'link':
        assert (data_source[:5].lower() == 'http:' or data_source[:6].lower() == 'https:'),\
            "The Data Graph source link must start with http: or https:"
        client_session = client_session or Session()
        try:
            response = client_session.get(data_source, headers={'Accept': 'text/turtle'})
            if not (200 <= response.status_code < 300):
                raise InvalidURLException("Data Graph Url got code {}".format(response.status_code), 406)
        except (ConnectionError, ConnectTimeout):
            raise InvalidURLException("Data Graph URL Not available.", 406)
        body = response.text
        data_source = body
    if shacl_graph_source == 'link':
        assert (shacl_source[:5].lower() == 'http:' or shacl_source[:6].lower() == 'https:'),\
            "The SHACL Graph source link must start with http: or https:"
        client_session = client_session or Session()
        try:
            response = client_session.get(shacl_source, headers={'Accept': 'text/turtle'})
            if not (200 <= response.status_code < 300):
                raise InvalidURLException("SHACL Url got code {}".format(response.status_code), 406)
        except (ConnectionError, ConnectTimeout):
            raise InvalidURLException("SHACL URL Not available.", 406)
        body = response.text
        shacl_source = body
    if extra_graph_source == 'link':
        assert (extra_source[:5].lower() == 'http:' or extra_source[:6].lower() == 'https:'),\
            "The Extra Ontology Graph source link must start with http: or https:"
        client_session = client_session or Session()
        try:
            response = client_session.get(extra_source, headers={'Accept': 'text/turtle'})
            if not (200 <= response.status_code < 300):
                raise InvalidURLException("Extra Ontology URL got code {}".format(response.status_code), 406)
        except (ConnectionError, ConnectTimeout):
            raise InvalidURLException("Extra Ontology URL Not available.", 406)
        body = response.text
        extra_source = body
    try:
        r = functions.run_validate(data_source, data_graph_format, shacl_source,
                                   shacl_graph_format,
                                   ont_graph=extra_source,
                                   ont_graph_format=extra_graph_format,
                                   inference=inference_data_option,
                                   enable_metashacl=enable_metashacl)
    except Exception as e:
        raise e
    conforms, report = r
    return Response(report, status=200,
                    headers={'Content-Type': 'application/ld+json'})


if __name__ == "__main__":
    logging.warning("Running the Flask app as an executable.\n"
                    "This is fine for debugging and testing, however "
                    "this is not the recommended way to run the Flask app.")
    app.run(host=CONFIG['APP_HOSTNAME'], port=CONFIG['APP_PORT'],
            debug=CONFIG['DEBUG'], use_reloader=False)




