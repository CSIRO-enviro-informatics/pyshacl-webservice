# encoding: utf-8
from pyshacl import validate
import json


def run_validate(target_graph_text, target_graph_format=None,
                 shacl_graph_text=None, shacl_graph_format=None,
                 inference=None, load_json=False):

    r = validate(target_graph_text, shacl_graph=shacl_graph_text,
                 inference=inference,
                 target_graph_format=target_graph_format,
                 shacl_graph_format=shacl_graph_format,
                 serialize_report_graph='json-ld')
    conforms, output, text = r
    if load_json:
        output = json.loads(output, encoding='utf-8')
    return conforms, output
