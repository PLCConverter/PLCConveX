import sys
sys.path.append('..')

import re
import argparse
import xml.etree.ElementTree as ET
import os
from LD.Schema.Elements import Variable, Type, POU, Interface
from Utils.token import tokenize_literals

from data.Lex.functions import STANDARD_FUNCTIONS
from data.Lex.keywords import ST_KEYWORDS
from Logs.colorLogger import get_color_logger
logger = get_color_logger("ST_Syntax")

gvars_path = '../data/Inters/vars.xml'
DEFAULT_INPUT = 'ST/Inputs/T_PLC_PRG.xml'
DEFAULT_OUTPUT = 'ST/Outputs/T_test.xml'
IDENTIFIER_PATTERN = re.compile(
    r"(?:[a-zA-Z]|_(?:[a-zA-Z]|[0-9]))(?:_?(?:[a-zA-Z]|[0-9]))*"
)

"""example ST language XML
<ST>s
    <xhtml >FB00();
IF con1 THEN
FB00();
END_IF;

func(in1:=con1,  out1=> var1);
</xhtml>
    </ST>

"""
class ST:
    def __init__(self, xhtml=None):
        self.xhtml = xhtml
    def __repr__(self):
        return f"ST(xhtml={self.xhtml})"
    def to_xml(self):
        st_element = ET.Element('ST')
        if self.xhtml is not None:
            xhtml_element = ET.Element('xhtml')
            xhtml_element.text = "__LT_PLACEHOLDER__" + self.xhtml + "__GT_PLACEHOLDER__"
            st_element.append(xhtml_element)
        return st_element
    @classmethod
    def parse(cls, element):
        xhtml = element.find('xhtml')
        if xhtml is not None:
            return cls(xhtml=xhtml.text)
        return cls(xhtml=None)
    
class Body:
    def __init__(self):
        self.ST = None
    def __repr__(self):
        return f"Body(ST={self.ST})"
    def to_xml(self):
        body_element = ET.Element('body')
        if self.ST is not None:
            body_element.append(self.ST.to_xml())
        return body_element
    

# find declared expressions in the interface
def get_declared_vars(interface: Interface) -> set:
    # init a empty set
    all_vars = set()
    for var_section in ['inputVars', 'localVars', 'outputVars', 'externalVars']:
        for var in getattr(interface, var_section):
            all_vars.add(var.name)
    return all_vars

def find_non_standard_functions(st_string):
    """
    Identify non-standard function calls in an ST language string.
    
    Args:
        st_string (str): The Structured Text string to analyze.
        standard_function_names (list or set): Collection of standard function names.
    
    Returns:
        list: List of tuples (function_name, start_pos, end_pos) for non-standard calls.
    """
    # Convert standard function names to a set for O(1) lookups
    standard_functions = set(STANDARD_FUNCTIONS)
    
    # Define the pattern for a function call: word followed by parentheses with content
    # \b ensures we match whole words
    # (\w+) captures the function name
    # \s* allows optional spaces before parentheses
    # \([^)]*\) matches the parentheses and their contents
    pattern = r'\b(\w+)\s*\([^)]*\)'
    
    # Find all function calls in the string
    matches = re.finditer(pattern, st_string)
    
    # List to store non-standard function calls
    non_standard_calls = []
    
    # Check each match
    for match in matches:
        function_name = match.group(1)  # Extract the function name
        if function_name not in standard_functions:
            # Record the name and its position in the string
            non_standard_calls.append(function_name)
    
    return non_standard_calls

def tokenize_st_code(code):
    """Tokenize ST code into words, operators, and punctuation, treating ':=' and '=>' as single tokens."""
    # Pattern explanation:
    # :=|=>          : Match ':=' or '=>' as single tokens
    # |\w+           : Match one or more word characters (letters, digits, underscores)
    # |[^\w\s]       : Match any single non-word, non-space character
    pattern = r':=|=>|\w+|[^\w\s]'
    tokens = re.findall(pattern, code, re.UNICODE)
    return tokens

def is_identifier(token):
    """Check if a token matches the variable identifier pattern."""
    return IDENTIFIER_PATTERN.fullmatch(token) is not None

def is_keyword(token):
    """Check if a token is an ST keyword (case-insensitive)."""
    return token.upper() in ST_KEYWORDS

def extract_variable_identifiers(code):
    """Extract variable identifiers from ST code, including those in function arguments."""
    tokens = tokenize_st_code(code)
    logger.debug(f"Tokens: {tokens}")
    variable_identifiers = []
    in_function_call = False
    function_call_depth = 0
    prev_token = None

    for i, token in enumerate(tokens):
        # Track function call context
        logger.debug(f"current token: {token}, prev token: {prev_token}")
        if token == '(' and prev_token and is_identifier(prev_token) and not is_keyword(prev_token):
            in_function_call = True
            function_call_depth = 1
        elif token == '(':
            if in_function_call:
                function_call_depth += 1
        elif token == ')':
            if in_function_call:
                function_call_depth -= 1
                if function_call_depth == 0:
                    in_function_call = False
        
        # Process potential variable identifiers
        if is_identifier(token) and not is_keyword(token) and not tokenize_literals(token):
            if in_function_call:
                # Case 1: Identifier after ':=' or '=>' is a variable
                logger.debug(f"current token: {token}, prev token: {prev_token}")
                if prev_token in [':=', '=>']:
                    variable_identifiers.append(token)
                # Case 2: Identifier not followed by ':=', '=>', or '(' is a positional argument
                elif i + 1 >= len(tokens) or tokens[i + 1] not in [':=', '=>', '(']:
                    variable_identifiers.append(token)
                # Identifiers followed by ':=' or '=>' are parameter names and skipped
            else:
                # Outside function calls, skip function names followed by '('
                if i + 1 < len(tokens) and tokens[i + 1] == '(':
                    prev_token = token
                    continue
                variable_identifiers.append(token)
        
        prev_token = token

    # Remove duplicates while preserving order
    seen = set()
    variable_identifiers = [x for x in variable_identifiers if not (x in seen or seen.add(x))]

    return variable_identifiers

"""
<variable name="func_FC">
    <type>
        <derived name="func" />
    </type>
</variable>
"""
def create_func_instance(interface: Interface, func_list = None) -> None:
    """
    create a variable with name ${function_name}_FC
    create a type with name ${function_name}
    """
    for func in func_list:
        type_el = ET.Element('type')
        derived_el = ET.Element('derived')
        derived_el.set('name', func)
        type_el.append(derived_el)
        var = Variable(name=f"{func}_FC")
        var.type = Type(element=type_el)
        # add to interface
        interface.localVars.append(var)

def modify_ST_func_call(st: ST, func_list = None) -> None:
    """
    Modify the function calls in the ST code to use the new function instances.
    """
    for func in func_list:
        st.xhtml = re.sub(r'\b' + func + r'\b', func + '_FC', st.xhtml)

def add_missing_vars(exist_vars, all_vars, interface: Interface):
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
                        interface.externalVars.append(Variable.parse(var))
                else:
                    logger.warning(f"Found variable without name: {var}")



# Example usage
def process_xml(input_file, output_file):
    logger.warning(f"{is_identifier('func')}")
    with open(input_file, 'r', encoding='utf-8') as f:
        xml_string = f.read()
    root = ET.fromstring(xml_string.strip())
    # Parse POU
    pou = POU(name=root.get('name'), pouType=root.get('pouType'))
    # Parse the <interface> and <body> sections
    st_el = None
    for child in root:
        if child.tag == 'interface':
            pou.interface = Interface.parse(child)
        elif child.tag == 'body':
            body = Body()
            st_el = child.find('ST')
            if st_el is not None:
                body.ST = ST.parse(st_el)
            pou.body = body
    repr(pou.body.ST)
    # get declared vars
    exist_vars = get_declared_vars(pou.interface)
    logger.debug(f"Declared vars: {exist_vars}")

    # Extract variable identifiers from the ST code
    code = pou.body.ST.xhtml
    variable_identifiers = extract_variable_identifiers(code)
    logger.debug(f"Variable identifiers: {variable_identifiers}")

    # Find non-standard function calls
    non_standard = find_non_standard_functions(code)
    pou_to_change_type = []
    for func_name in non_standard:
        logger.debug(f"Non-standard function: {func_name}")
        if func_name not in exist_vars:
            logger.debug(f"Creating function instance for {func_name}")
            pou_to_change_type.append(func_name)
    create_func_instance(pou.interface, pou_to_change_type)
    modify_ST_func_call(pou.body.ST, pou_to_change_type)
    # write pou_to_change_type to an output file
    with open("ST/Outputs/change.txt", 'w', encoding='utf-8') as f:
        f.write("\n".join(pou_to_change_type))
    
    # add missing vars
    all_vars = variable_identifiers
    all_vars = sorted(all_vars)
    logger.debug(f"All vars: {all_vars}")
    add_missing_vars(exist_vars, all_vars, pou.interface)
    
    # regenerate the XML
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