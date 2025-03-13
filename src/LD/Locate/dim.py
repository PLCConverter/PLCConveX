# dim.py
# This module defines dimensions and port settings (relative positions) for various element types.
# Each key is a tuple (tag, typename) where typename can be None.
import xml.etree.ElementTree as ET

DIMENSIONS = {
    ("leftPowerRail", None): {
        "width": 10,
        "height": 100
    },
    # Blocks with specific types:
    ("block", "MOVE"): {
        "width": 60,
        "height": 60,
        0: 30,
        1: 50,
        "ENO": 30,
        "OUT": 50
    },
    ("block", "TON"): {
        "width": 50,
        "height": 60,
        0: 30,
        1: 50
    },
    ("block", "R_TRIG"): {
        "width": 60,
        "height": 40,
        "Q": 30,
        0: 30
    },
    ("block", "F_TRIG"): {
        "width": 60,
        "height": 40,
        "Q": 30,
        0: 30
    },
    ("block", "EQ"): {
        "width": 70,
        "height": 80,
        "OUT": 50
    },
    ("block", "GT"): {
        "width": 70,
        "height": 80,
        "OUT": 50
    },
    ("block", "LT"): {
        "width": 70,
        "height": 80,
        "OUT": 50
    },
    ("block", "GE"): {
        "width": 70,
        "height": 80,
        "OUT": 50
    },
    ("block", "LE"): {
        "width": 70,
        "height": 80,
        "OUT": 50
    },
    ("block", "NE"): {
        "width": 70,
        "height": 80,
        "OUT": 50
    },
    ("block", "ADD"): {
        "width": 70,
        "height": 80,
        0: 30,
        1: 50,
        "OUT": 50
    },
    ("block", "SUB"): {
        "width": 70,
        "height": 80,
        0: 30,
        1: 50,
        "OUT": 50
    },
    ("block", "MUL"): {
        "width": 70,
        "height": 80,
        0: 30,
        1: 50,
        "OUT": 50
    },
    ("block", "DIV"): {
        "width": 70,
        "height": 80,
        0: 30,
        1: 50,
        "OUT": 50
    },
    ("block", "MOD"): {
        "width": 70,
        "height": 80,
        0: 30,
        1: 50,
        "OUT": 50
    },
    # Default block definition:
    ("block", None): {
        "width": 60,
        "height": 60,
        "OUT": 30,
        "port": {
            "in": {"x": 0, "y_factor": 0.5},
            "out": {"x": 60, "y_factor": 0.5}
        }
    },
    # Other elements:
    ("coil", None): {
        "width": 30,
        "height": 20,
        "port": {
            "in": {"x": 0, "y_factor": 0.5},
            "out": {"x": 30, "y_factor": 0.5}
        }
    },
    ("contact", None): {
        "width": 30,
        "height": 20,
        "port": {
            "in": {"x": 0, "y_factor": 0.5},
            "out": {"x": 30, "y_factor": 0.5}
        }
    },
    ("inVariable", None): {
        "width": 50,
        "height": 30,
        0: 20
    },
    ("outVariable", None): {
        "width": 50,
        "height": 30,
        0: 20
    },
    # Fallback for any other element:
    ("default", None): {
        "width": 30,
        "height": 20,
        "port": {
            "in": {"x": 0, "y_factor": 0.5},
            "out": {"x": 30, "y_factor": 0.5}
        }
    }
}

def get_dimensions(tag, typename=None):
    """
    Retrieve dimensions for a given tag and optional typename.
    """
    key = (tag, typename)
    if key in DIMENSIONS:
        return DIMENSIONS[key]
    key = (tag, None)
    if key in DIMENSIONS:
        return DIMENSIONS[key]
    return DIMENSIONS[("default", None)]

def get_port_positions(node):
    """
    For non-block nodes, return the default port settings.
    Returns a tuple: (input_port, output_port) where each is a dict with keys 'x' and 'y_factor'.
    """
    dims = get_dimensions(node.tag, node.attrib.get("typeName"))
    if "port" in dims:
        in_port = dims["port"].get("in", {"x": 0, "y_factor": 0.5})
        out_port = dims["port"].get("out", {"x": dims.get("width", 30), "y_factor": 0.5})
    else:
        in_port = {"x": 0, "y_factor": 0.5}
        out_port = {"x": dims.get("width", 30), "y_factor": 0.5}
    return in_port, out_port

def compute_block_port_y(element: ET.Element, count, index) -> int:
    """
    Compute the y position for a block's port given the node height,
    the total number of ports (count), and the zero-based index of the port.
    """
    key = (element.tag, element.attrib.get("typeName"))
    default_height = 60
    if key in DIMENSIONS:
        if index in DIMENSIONS[key]:
            return DIMENSIONS[key][index]
    return default_height // (index + 1)
    
        
