import sys
sys.path.append("../")

import re
from LD.Schema.Elements import Type, Variable
import xml.etree.ElementTree as ET
import os
import glob

from Logs.colorLogger import get_color_logger
logger = get_color_logger("postprocess.py")


FILE_PATH = "../data/Outputs/plc.xml"
FINAL_PATH = "D:/PLCworks/result/plc.xml"
REPLACE_TAG = {
    "xhtml":"xhtml:p"
}
REPLACE_PLACEHOLDER = {
    "__GT_PLACEHOLDER__":"]]>",
    "__LT_PLACEHOLDER__":"<![CDATA[",
    "&lt;":"<",
    "&gt;":">"
}

def replace_placeholders(text):
    # Combine both replacement dictionaries
    replace_dict = {**REPLACE_TAG, **REPLACE_PLACEHOLDER}
    # Create a regex pattern that matches any key
    pattern = '|'.join(re.escape(key) for key in replace_dict.keys())
    
    # Define a function to return the replacement value for a match
    def replacer(match):
        return replace_dict[match.group(0)]
    
    # Perform all replacements in a single pass
    return re.sub(pattern, replacer, text)
            
def add_namespaces(text):

    """ xmlns="http://www.plcopen.org/xml/tc6_0201" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:ns1="http://www.plcopen.org/xml/tc6_0201"
    """
    # replace project with project with namespaces from the position of project
    text_namespace = 'xmlns="http://www.plcopen.org/xml/tc6_0201" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:ns1="http://www.plcopen.org/xml/tc6_0201"'
    return re.sub(r'<project', f'<project {text_namespace}', text, count=1)
    
  
def main(input_file = FILE_PATH, output_file = FINAL_PATH):
    # read input xml file as string
    with open(input_file, "r") as f:
        xml_str = f.read()
    xml_str = replace_placeholders(xml_str)

    xml_str = add_namespaces(xml_str)
    # write the modified string to the output file
    with open(output_file, "w") as f:
        f.write(xml_str)
    logger.info(f"Final result written to {output_file}")

if __name__ == "__main__":  
    main()