# -*- coding: utf-8 -*-
from pyshacl import validate
from pyshacl.errors import ReportableRuntimeError, ValidationFailure, ConstraintLoadError, ShapeLoadError
import json


def run_validate(data_graph_text, data_graph_format=None,
                 shacl_graph_text=None, shacl_graph_format=None,
                 ont_graph=None, ont_graph_format=None,
                 inference=None, enable_metashacl=False, advanced=True,
                 load_json=False):

    try:
        r = validate(data_graph_text, shacl_graph=shacl_graph_text,
                     inference=inference,
                     data_graph_format=data_graph_format,
                     shacl_graph_format=shacl_graph_format,
                     ont_graph=ont_graph, ont_graph_format=ont_graph_format,
                     serialize_report_graph='json-ld',
                     meta_shacl=enable_metashacl, advanced=advanced)
        conforms, output, text = r
    except ValidationFailure as vf:
        conforms = False
        output = {
            "error": "ValidationFailure",
            "message": str(vf.message)
        }
        output = json.dumps(output)
    except ConstraintLoadError as cl:
        conforms = False
        output = {
            "error": "ConstraintLoadError",
            "message": "{}\n{}".format(str(cl.message), str(cl.link))
        }
        output = json.dumps(output)
    except ShapeLoadError as sl:
        conforms = False
        output = {
            "error": "ShapeLoadError",
            "message": "{}\n{}".format(str(sl.message), str(sl.link))
        }
        output = json.dumps(output)
    except ReportableRuntimeError as rre:
        conforms = False
        output = {
            "error": "ReportableRuntimeError",
            "message": str(rre.message)
        }
        output = json.dumps(output)
    except RuntimeError as re:
        conforms = False
        output = {
            "error": "RuntimeError",
            "message": "An unknown error occurred."
        }
        output = json.dumps(output)

    if load_json:
        output = json.loads(output, encoding='utf-8')
    return conforms, output
