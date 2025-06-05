import argparse
import sys
sys.path.append("../")
import os
from LD.Schema.Elements import Type, Variable
import xml.etree.ElementTree as ET

from enum import Enum

from Logs.colorLogger import get_color_logger
logger = get_color_logger("PREPROCESS")

# Define the elements to be removed
# !!! WARNING: vendorElement maybe reinstated in the future !!!
class LanCategory(Enum):
    """Enumeration of the different PLC languages."""
    LD = "LD"
    FBD = "FBD"
    IL = "IL"
    SFC = "SFC"
    ST = "ST"

GLOBAL_SLASH_LIST = ["addData", "rightPowerRail", "vendorElement"]
LD_OUTPUT_DIR = "LD/Inputs"
ST_OUTPUT_DIR = "ST/Inputs" 
DEFAULT_TASK_INPUT = "../data/Inputs/TASK.xml"

gv_root = ET.Element("resource")
# Load the XML file
DEFAULT_INPUT = "../data/Inputs/PIDControl.xml"
var_output = "../data/Inters/vars.xml"
type_output = "Type/Inputs/types.xml"
task_output = "Task/Inputs/tasks.xml"

def extract_datatype_elements(root: ET.Element, output_dir = type_output):
    dts = ET.Element("dataTypes")
    for dt in root.findall(".//dataType"):
        dts.append(dt)
    types = ET.Element("types")
    types.append(dts)
    ET.ElementTree(types).write(output_dir, encoding="utf-8", xml_declaration=False)

def extract_pou_elements(root: ET.Element, output_dir = None):
    """
    Extract all <pou> elements from an XML file and save them to separate files.
    
    Args:
        input_file (str): Path to the input XML file
        output_dir (str): Directory to store the extracted POU files
    """
    def categorize(root: ET.Element) -> LanCategory:
        body = root.find("body")
        if body is None:
            logger.error("Body element not found in XML tree.")
            return None
        lan_LD = body.find("LD")
        if lan_LD is not None:
            return LanCategory.LD
        lan_ST = body.find("ST")
        if lan_ST is not None:
            return LanCategory.ST
        return None


    # Find all pou elements using XPath expression
    for pou in root.findall(".//pou"):
        # Extract the name attribute
        name = pou.get("name")
        if name:
            category = categorize(pou)
            target_dir = output_dir
            if target_dir is None:
                if category == LanCategory.LD:
                    target_dir = LD_OUTPUT_DIR
                elif category == LanCategory.ST:
                    target_dir = ST_OUTPUT_DIR
                else:
                    logger.error(f"Unknown language category for POU '{name}'. Skipping.")
                    continue
            # Create dir and output filename
            os.makedirs(target_dir, exist_ok=True)
            output_file = os.path.join(target_dir, f"T_{name}.xml")
            pou_tree = ET.ElementTree(pou)
            # Write to output file
            pou_tree.write(output_file, encoding="utf-8", xml_declaration=False)
            logger.debug(f"Extracted POU '{name}' to {output_file}")

def deal_mixed_globalVars(root: ET.Element) -> None:
    logger.debug("Processing MixedAttrsVarList.")
    if root.tag != "MixedAttrsVarList":
        logger.error(f"Root tag is {root.tag} NOT'MixedAttrsVarList'. Failed to process mixAttrList.")
        return
    gvs = root.findall("globalVars")
    for gv in gvs:
        retain = gv.get("retain") == "true"
        constant = gv.get("constant") == "true"
        deal_globalVars(gv, retain, constant)
        



# extract global vars
''' example
<project xmlns="http://www.plcopen.org/xml/tc6_0200">
  <addData>
    <data name="http://www.3s-software.com/plcopenxml/application" handleUnknown="implementation">
      <resource name="Application">
        <globalVars name="GVL_FB">
          <variable name="线体气缸初始_A">
            <type>
              <derived name="FB_线体气缸初始化" />
            </type>
          </variable>
          <variable name="线体气缸初始_B">
            <type>
              <derived name="FB_线体气缸初始化" />
            </type>
          </variable>
          <variable name="对接气缸初始_C">
            <type>
              <derived name="FB_对接气缸初始化" />
            </type>
          </variable>
          <variable name="取料模组初始化_A">
            <type>
              <derived name="FB_取料模组初始化" />
            </type>
          </variable>
          <variable name="取料模组初始化_B">
            <type>
              <derived name="FB_取料模组初始化" />
            </type>
          </variable>
          <variable name="主线模组初始化_C">
            <type>
              <derived name="FB_主线模组初始化" />
            </type>
          </variable>
        </globalVars>
'''

def deal_globalVars(root: ET.Element, retain = False, constant = False) -> None:
    if root.tag != "globalVars":
        logger.error("Root tag is not 'globalVars'. Failed to extract global vars.")
        return

    # First, check if there's MixedAttrsVarList.
    is_mixed = False
    for elem in root:
        if elem.tag == "addData":
            data = elem.find("data")
            if data is not None:
                mix = data.find("MixedAttrsVarList")
                if mix is not None:
                    is_mixed = True
                    deal_mixed_globalVars(mix)
    if is_mixed:
        return
    # construct the globalVars element based on the retain and constant attributes
    global_vars = ET.Element("globalVars")
    if retain:
        global_vars.set("retain", "true")
    if constant:
        global_vars.set("constant", "true")

    for var in root:
        if var.tag == "variable":
            # append the variable to 
            global_vars.append(var)
        else:
            pass
    # append globalVars to the gv_root
    gv_root.append(global_vars)
                            
def extract_global_vars(root: ET.Element) -> None:
    if root.tag != "project":
        logger.error(f"Root tag is {root.tag} NOT 'project'. Failed to extract global vars.")
        return
    for elem in root:
        if elem.tag == "addData":
            datas = elem.findall("data")
            for data in datas:
                resources = data.findall("resource")
                for resource in resources:
                    gvs = resource.findall("globalVars")
                    for gv in gvs:
                        retain = gv.get("retain") == "true"
                        constant = gv.get("constant") == "true"
                        deal_globalVars(gv, retain, constant)
    # write the gv_root to file from the beginning
    ET.ElementTree(gv_root).write(var_output, encoding='utf-8', xml_declaration=False)


def remove_unsupported_elements(parent):
    """Recursively remove unsupported elements from the XML tree."""
    for elem in list(parent):
        if elem.tag in GLOBAL_SLASH_LIST:
            parent.remove(elem)
        else:
            remove_unsupported_elements(elem)  # Recursively check children

def strip_namespace(root: ET.Element) -> str:
    # Parse the XML string into an ElementTree object
    logger.debug("Stripping namespace from XML tree.")
    
    # Iterate through all elements in the XML tree
    for elem in root.iter():
        # Check if the tag includes a namespace (indicated by '}')
        if '}' in elem.tag:
            # Extract the local name by splitting at '}' and taking the part after it
            elem.tag = elem.tag.split('}', 1)[1]
    
    # Serialize the modified tree back to a string
    return ET.tostring(root, encoding='unicode')

def deal_task(input_file = DEFAULT_TASK_INPUT):
    # find if the input file exists
    if not os.path.exists(input_file):
        logger.warning(f"Input file {input_file} does not exist. Skipping task processing.")
        return
    
    root = ET.parse(input_file).getroot()
    # strip the namespace
    modified_xml = strip_namespace(root)
    # write the modified XML to a file
    logger.info(f"Writing modified XML to {task_output}.")
    with open(task_output, 'w', encoding='utf-8') as f:
        f.write(modified_xml) 

# Convert formalParameter attributes
FORMALPARAMETER_MAP = {
    'Out1': 'OUT',
    'Out2': 'OUT',
}

def convert_formal_parameter(elem: ET.Element) -> None:
    # check the tag of the element
    if elem.tag == "inputVariables":
        fp_list = []
        var_list = elem.findall("variable")
        for vars in var_list:
            fp = vars.get("formalParameter")
            if fp is not None:
                fp_list.append(fp)
        # check if In3 is in the list
        if "In3" in fp_list:
            print("Converting formalParameter 'In3' to 'IN2', 'In2' to 'IN1'.")
            for vars in var_list:
                if vars.get("formalParameter") == "In2":
                    vars.set("formalParameter", "IN1")
                if vars.get("formalParameter") == "In3":
                    vars.set("formalParameter", "IN2")
        else:
            for vars in var_list:
                if vars.get("formalParameter") == "In2":
                    print("Converting formalParameter 'In2' to 'IN'.")
                    vars.set("formalParameter", "IN")
        return
    
    fp = elem.get("formalParameter")
    if fp is None:
        return
    if fp in FORMALPARAMETER_MAP:
        print(f"Converting formalParameter '{fp}' to '{FORMALPARAMETER_MAP[fp]}'.")
        elem.set("formalParameter", FORMALPARAMETER_MAP[fp])

def convert_fp_tree(root: ET.Element):
    if root is None:
        return
    convert_formal_parameter(root)
    for child in list(root):
        convert_fp_tree(child)


# start of main
def main_routine(input_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    modified_xml = strip_namespace(root)
    root = ET.fromstring(modified_xml)
    # clear var_out file
    with open(var_output, 'w', encoding='utf-8') as f:
        f.write("")
    # extract global vars
    extract_global_vars(root)
    # extract pou elements
    extract_pou_elements(root)
    # extract data type elements
    extract_datatype_elements(root)
    # deal with task elements FROM ANOTHER FILE
    deal_task(DEFAULT_TASK_INPUT)
    # TBD: extract configuration elements           

def main():
    parser = argparse.ArgumentParser(
        description="Designate the source project file to convert."
    )
    parser.add_argument(
        '-i', '--input',
        default=DEFAULT_INPUT,
        help='Input source project file path (default: %(default)s)'
    )

    args = parser.parse_args()
    input_file = args.input
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} does not exist. Exiting.")
        sys.exit(1)

    main_routine(input_file)

if __name__ == "__main__":
    main()