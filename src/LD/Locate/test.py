import sys
sys.path.append('..')
import argparse

import xml.etree.ElementTree as ET
from LD.Locate.Locate import Locator

DEFAULT_INPUT = 'LD/Inters/intermediate.xml'
DEFAULT_OUTPUT = 'LD/Outputs/LD_CONVERTED.xml'

from Logs.colorLogger import get_color_logger
logger = get_color_logger("Locate/test.py")

xml_string = '''<pou name="program0" pouType="program">
        <interface>
          <localVars>
            <variable name="out1">
              <type>
                <INT/>
              </type>
            </variable>
          </localVars>
        </interface>
        <body>
          <LD>
            <leftPowerRail localId="0" height="119" width="16">
              <position x="229" y="109"/>
              <connectionPointOut formalParameter="">
                <relPosition x="16" y="20"/>
              </connectionPointOut>
            </leftPowerRail>
            <block localId="3" typeName="MOVE" height="60" width="55">
              <position x="346" y="99"/>
              <inputVariables>
                <variable formalParameter="EN">
                  <connectionPointIn>
                    <relPosition x="0" y="30"/>
                    <connection refLocalId="0">
                      <position x="346" y="129"/>
                      <position x="245" y="129"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="IN">
                  <connectionPointIn>
                    <relPosition x="0" y="50"/>
                    <connection refLocalId="4">
                      <position x="346" y="149"/>
                      <position x="312" y="149"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="ENO">
                  <connectionPointOut>
                    <relPosition x="55" y="30"/>
                  </connectionPointOut>
                </variable>
                <variable formalParameter="OUT">
                  <connectionPointOut>
                    <relPosition x="55" y="50"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <inVariable localId="4" height="26" width="50" negated="false">
              <position x="262" y="136"/>
              <connectionPointOut>
                <relPosition x="50" y="13"/>
              </connectionPointOut>
              <expression>INT#2</expression>
            </inVariable>
            <outVariable localId="5" height="26" width="42" negated="false">
              <position x="468" y="137"/>
              <connectionPointIn>
                <relPosition x="0" y="13"/>
                <connection refLocalId="3" formalParameter="OUT">
                  <position x="468" y="150"/>
                  <position x="434" y="150"/>
                  <position x="434" y="149"/>
                  <position x="401" y="149"/>
                </connection>
              </connectionPointIn>
              <expression>out1</expression>
            </outVariable>
          </LD>
        </body>
      </pou>'''

REQUIRED_SPEC = {
    'block': {
        'attributes': {
            'typeName': 'undefined',
            'localId': 'undefined'
        },
        'children': {
            'position': {
                'attributes': {},
                'children': {}  # No required grandchildren in this example.
            },
            'inputVariables': {
                'attributes': {},
                'children': {}  # Could add default structure for variables if needed.
            },
            'inOutVariables': {
                'attributes': {},
                'children': {}
            },
            'outputVariables': {
                'attributes': {},
                'children': {}
            }
        },
        'order': ['position', 'inputVariables', 'inOutVariables', 'outputVariables']
    },
    # You can add specs for other element types if needed.
}

def ensure_required_structure(elem: ET.Element, spec: dict):
    """
    Check an element against a specification (spec) and add missing attributes/children.
    The spec is expected to be a dict with 'attributes' and 'children' keys.
    """
    # Ensure required attributes
    required_attrs = spec.get('attributes', {})
    for attr, default_val in required_attrs.items():
        if attr not in elem.attrib:
            logger.debug(f"Adding missing attribute '{attr}' to <{elem.tag}> with default value '{default_val}'.")
            elem.attrib[attr] = default_val

    # Ensure required children
    # The logic below ensures that the children are in the correct order, UNDER THE assumption that every child in the 'order' ONLY APPEAR ONCE!
    required_children = spec.get('children', {})
    for child_tag, child_spec in required_children.items():
        child = elem.find(child_tag)
        if child is None:
            logger.debug(f"Adding missing child <{child_tag}> to <{elem.tag}>.")
            child = ET.Element(child_tag)
            # get the index of current child
            index = spec['order'].index(child_tag)
            # Set default attributes for the new child.
            for a, default_val in child_spec.get('attributes', {}).items():
                child.attrib[a] = default_val
            # insert the newly created child at suitable index
            elem.insert(index, child)
        # Recursively ensure the structure for the child element.
        ensure_required_structure(child, child_spec)

def patch_tree(root: ET.Element, spec_map: dict):
    """
    Recursively walk through the XML tree.
    For every element whose tag appears in spec_map,
    enforce the required structure.
    """
    # check if current element's tag is comment
    # if so, remove current element
    # WARN: temporary solution, should have another function doing post-processing job
    if root.tag == 'LD':
        for child in root:
            if child.tag == 'comment':
                root.remove(child)
        

    if root.tag in spec_map:
        ensure_required_structure(root, spec_map[root.tag])
    for child in root:
        patch_tree(child, spec_map)

def process_xml(input_file, output_file):
    # Read the XML (either from a file or a string)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    root = ET.fromstring(xml_string.strip())
    ld = root.find("body").find("LD")
    assert(ld is not None)
    locator = Locator(ld)
    locator.locate()
    patch_tree(root, REQUIRED_SPEC)

    # clear the file and write the new content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(ET.tostring(root, encoding='unicode').strip())

def main():
    parser = argparse.ArgumentParser(
        description="Process XML file by removing unsupported elements and converting formal parameters."
    )
    parser.add_argument(
        '-i', '--input',
        default=DEFAULT_INPUT,
        help='Input XML file path (default: %(default)s)'
    )
    parser.add_argument(
        '-o','--output',
        default=DEFAULT_OUTPUT,
        help='Output XML file path (default: %(default)s)'
    )
    args = parser.parse_args()
    if args.input != DEFAULT_INPUT and args.output == DEFAULT_OUTPUT:
        args.output = args.input.replace("_intermediate", "_out").replace("Inters", "Outputs")
        logger.debug(f"Output file path: {args.output}")
    process_xml(args.input, args.output)

if __name__ == "__main__":
    main()