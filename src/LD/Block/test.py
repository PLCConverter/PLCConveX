import sys
sys.path.append('..')
sys.path.append('../..')
import argparse
import xml.etree.ElementTree as ET

from LD.Schema.Elements import Variable, Type, Connection, ConnectionPointIn, ConnectionPointOut, RelPosition, Expression, OutVariable, InVariable, Block, LD, POU, Interface, Coil, Contact
from LD.Utils.counter import get_value, set_value
from LD.Variables.token import tokenize_literals
import os
from enum import Enum

from Logs.colorLogger import get_color_logger
logger = get_color_logger("Block/test.py")

class Body:
    def __init__(self):
        self.LD = None
    def __repr__(self):
        return f"Body(LD={self.LD})"
    def to_xml(self):
        body_element = ET.Element('body')
        if self.LD is not None:
            body_element.append(self.LD.to_xml())
        return body_element

# -----------------------------
# Main XML Analysis
# -----------------------------

# Read the XML
DEFAULT_INPUT = 'LD/Inters/preprocess.xml'
DEFAULT_OUTPUT = 'LD/Inters/intermediate.xml'
gvars_path = '../data/Inters/vars.xml'

# find declared expressions in the interface
def get_declared_vars(interface: Interface) -> set:
    # init a empty set
    all_vars = set()
    for var_section in ['inputVars', 'localVars', 'outputVars', 'externalVars']:
        for var in getattr(interface, var_section):
            all_vars.add(var.name)
    return all_vars

def get_all_vars(LD: LD) -> set:
    all_vars = set()
    for elem in LD.elements:
        if isinstance(elem, Coil):
            if elem.variable is not None:
                all_vars.add(elem.variable)
            else:
                logger.warning(f"Coil element without variable: {elem}")
        elif isinstance(elem, Contact):
            if elem.variable is not None:
                all_vars.add(elem.variable)
            else:
                logger.warning(f"Contact element without variable: {elem}")
        elif isinstance(elem, Block):
            exps = elem.get_expressions()
            for exp in exps:
                if exp is not None:
                    if tokenize_literals(exp) == False:
                        all_vars.add(exp)
    return all_vars



# Further LD processing
class BlockCategory(Enum):
    CMP = 1
    MATH = 2
    TIMER = 3
    TRIG = 4
    OTHER = 5

def classify_block(block: Block) -> BlockCategory:
    t = block.typeName.upper()
    if t in ['GT', 'EQ', 'GE', 'LE', 'NE', 'LT']:
        return BlockCategory.CMP
    elif t in ['ADD', 'SUB', 'DIV', 'MUL', 'MOD', 'MOVE']:
        return BlockCategory.MATH
    elif t == "TON":
        return BlockCategory.TIMER
    elif t in ['R_TRIG', 'F_TRIG']:
        return BlockCategory.TRIG
    else:
        return BlockCategory.OTHER
    
def classify_block_element(elem: ET.Element) -> BlockCategory:
    t = elem.get('typeName')
    if t in ['GT', 'EQ', 'GE', 'LE', 'NE', 'LT']:
        return BlockCategory.CMP
    elif t in ['ADD', 'SUB', 'DIV', 'MUL', 'MOD', 'MOVE']:
        return BlockCategory.MATH
    elif t == "TON":
        return BlockCategory.TIMER
    elif t in ['R_TRIG', 'F_TRIG']:
        return BlockCategory.TRIG
    else:
        return BlockCategory.OTHER

def addOutVariable(block: Block):
    global nextID
    category = classify_block(block)
    if category == BlockCategory.MATH:
        for outVar in block.outputVariables:
            if outVar.connectionPointOut and outVar.connectionPointOut.expression is not None:
                fp = outVar.formalParameter
                logger.debug(f"[MATH] Found output variable with formalParameter '{fp}' .")
                newOut = OutVariable(localId=str(nextID), height="20", width="40", negated="false")
                newOut.expression = Expression(outVar.connectionPointOut.expression.text)
                nextID += 1
                newCPI = ConnectionPointIn()
                newCPI.relPosition = RelPosition(0, 10)
                newCon = Connection(refLocalId=block.localId, formalParameter=fp)
                newCPI.connections.append(newCon)
                newOut.connectionPointIn = newCPI
                return newOut
    elif category == BlockCategory.CMP:
        ENO_var = None
        for outVar in block.outputVariables:
            if outVar.formalParameter == "ENO":
                ENO_var = outVar
                break
        if ENO_var is None:
            logger.debug(f"[CMP] Adding ENO variable to block.")
            ENO_var = Variable(formalParameter="ENO")
            newCPO = ConnectionPointOut()
            newCPO.relPosition = RelPosition(10, 10)
            ENO_var.connectionPointOut = newCPO
            block.outputVariables.append(ENO_var)
        return None
    elif category == BlockCategory.TIMER:
        logger.debug(f"[TIMER] Found TIMER block.")
        pass
    return None

def LD_convert(LD_element: LD) -> LD:
    global nextID
    global_max_id = get_value()
    logger.debug(f"max localID is {global_max_id}")
    nextID = global_max_id + 1
    new_LD = LD()
    for elem in LD_element.elements:
        if isinstance(elem, Block):
            ret = addOutVariable(elem)
            if ret is not None:
                new_LD.elements.append(ret)
        new_LD.elements.append(elem)
    return new_LD

def process_xml(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    root = ET.fromstring(xml_string.strip())

    # Initialize global_max_id
    set_value(0)

    # Parse POU
    pou = POU(name=root.get('name'), pouType=root.get('pouType'))
    # Parse the <interface> and <body> sections
    for child in root:
        if child.tag == 'interface':
            pou.interface = Interface.parse(child)
        elif child.tag == 'body':
            body = Body()
            ld_el = child.find('LD')
            if ld_el is not None:
                body.LD = LD.parse(ld_el)
            pou.body = body
    target_LD = LD_convert(pou.body.LD)
    pou.body.LD = target_LD

    exist_vars = get_declared_vars(pou.interface)
    all_vars = get_all_vars(pou.body.LD)
    # sort
    exist_vars = sorted(exist_vars)
    all_vars = sorted(all_vars)
    logger.debug(f"Declared vars: {exist_vars}")
    logger.debug(f"All vars: {all_vars}")
    # find missing vars, add them from gvars
    missing_vars = [var for var in all_vars if var not in exist_vars]
    logger.debug(f"Missing vars: {missing_vars}")
    if missing_vars:
        with open(gvars_path, 'r', encoding='utf-8') as f:
            gvars_string = f.read()
        gvars_root = ET.fromstring(gvars_string.strip())
        for gvs in gvars_root:
            if gvs.tag != 'globalVars':
                continue
            for var in gvs:
                if name := var.get('name'):
                    if name in missing_vars:
                        logger.debug(f"Adding missing var '{name}' to interface.")
                        pou.interface.externalVars.append(Variable.parse(var))
                else:
                    logger.warning(f"Found variable without name: {var}")
    # insert the gvars to external vars list of interface

    # Write out the resulting XML
    pou_element = pou.to_xml()
    xml_str = ET.tostring(pou_element, encoding='utf-8')
    fd = os.open(output_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    os.write(fd, xml_str)

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
        args.output = args.input.replace("_preprocess", "_intermediate")
        logger.debug(f"Output file path: {args.output}")
    process_xml(args.input, args.output)

if __name__ == "__main__":
    main()

''' example gvars
<resource>
  <globalVars retain="true">
    <variable name="con1">
      <type>
        <BOOL />
      </type>
      <initialValue>
        <simpleValue value="TRUE" />
      </initialValue>
    </variable>
  </globalVars>
  <globalVars constant="true">
    <variable name="con2">
      <type>
        <BOOL />
      </type>
      <initialValue>
        <simpleValue value="TRUE" />
      </initialValue>
    </variable>
  </globalVars>
  <globalVars>
    <variable name="norm1">
      <type>
        <INT />
      </type>
    </variable>
  </globalVars>
</resource>
'''