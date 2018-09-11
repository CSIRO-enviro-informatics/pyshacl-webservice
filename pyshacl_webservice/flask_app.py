# encoding: utf-8
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
from flask import Flask, Response, request
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

@app.route('/', methods={'GET'})
def index():
    return app.send_static_file('index.html')

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
        target_graph_source = form['targetGraphSource']
        assert target_graph_source, "targetGraphSource not found in form data."
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    try:
        shacl_graph_source = form['shaclGraphSource']
    except (AttributeError, KeyError, AssertionError) as e:
        raise e

    assert target_graph_source in {'text', 'file', 'link'}, "Unsupported Target Graph source."
    assert shacl_graph_source in {'text', 'file', 'link', 'none', None}, "Unsupported SHACL Graph source."

    try:
        target_graph_format = form['targetGraphFormat']
        assert target_graph_format, "targetGraphFormat not found in form data."
    except (AttributeError, KeyError, AssertionError) as e:
        raise e

    try:
        inference_target_option = form['inferenceTargetOption']
        assert inference_target_option, "inferenceTargetOption not found in form data."
    except (AttributeError, KeyError, AssertionError) as e:
        raise e
    if target_graph_source == 'file':
        try:
            target_data = request.files['targetData']
            assert target_data
            target_data = target_data.read()
        except (AttributeError, KeyError, AssertionError):
            raise FileNotFoundError('Target Data File not found')
        if isinstance(target_data, bytes):
            # Assuming UTF-8 here, this might not always be right.
            target_data = target_data.decode('utf-8')
    else:
        try:
            target_data = form['targetData']
            assert target_data, 'targetData not found in the form data.'
        except (AttributeError, KeyError, AssertionError) as e:
            raise e
    if (not shacl_graph_source) or shacl_graph_source == 'none':
        shacl_data = None
        shacl_graph_format = None
    else:
        try:
            shacl_graph_format = form['shaclGraphFormat']
            assert shacl_graph_format, "shaclGraphFormat not found in form data."
        except (AssertionError, KeyError, AssertionError) as e:
            raise e
        if shacl_graph_source == 'file':
            try:
                shacl_data = request.files['shaclData']
                assert shacl_data
                shacl_data = shacl_data.read()
            except (AttributeError, KeyError, AssertionError):
                raise FileNotFoundError('SHACL Data File not found')
            if isinstance(shacl_data, bytes):
                # Assuming UTF-8 here, this might not always be right.
                shacl_data = shacl_data.decode('utf-8')
        else:
            try:
                shacl_data = form['shaclData']
                assert shacl_data, 'shaclData not found in the form data.'
            except (AttributeError, KeyError, AssertionError) as e:
                raise e
    client_session = None
    if target_graph_source == 'link':
        assert (target_data[:5].lower() == 'http:' or target_data[:6].lower() == 'https:'),\
            "The Target Graph source link must start with http: or https:"
        client_session = client_session or Session()
        try:
            response = client_session.get(target_data, headers={'Accept': 'text/turtle'})
            if not (200 <= response.status_code < 300):
                raise InvalidURLException("Target Url got code {}".format(response.status_code), 406)
        except (ConnectionError, ConnectTimeout):
            raise InvalidURLException("Target URL Not available.", 406)
        body = response.text
        target_data = body
    if shacl_graph_source == 'link':
        assert (shacl_data[:5].lower() == 'http:' or shacl_data[:6].lower() == 'https:'),\
            "The SHACL Graph source link must start with http: or https:"
        client_session = client_session or Session()
        try:
            response = client_session.get(shacl_data, headers={'Accept': 'text/turtle'})
            if not (200 <= response.status_code < 300):
                raise InvalidURLException("SHACL Url got code {}".format(response.status_code), 406)
        except (ConnectionError, ConnectTimeout):
            raise InvalidURLException("SHACL URL Not available.", 406)
        body = response.text
        shacl_data = body
    try:
        r = functions.run_validate(target_data, target_graph_format, shacl_data,
                                   shacl_graph_format, inference_target_option)
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




