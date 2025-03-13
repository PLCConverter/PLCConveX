import sys
sys.path.append("../")

from LD.Schema.Elements import Type, Variable
import xml.etree.ElementTree as ET


from Logs.colorLogger import get_color_logger
logger = get_color_logger("PREPROCESS")

# Define the elements to be removed
# !!! WARNING: vendorElement maybe reinstated in the future !!!
GLOBAL_SLASH_LIST = ["addData", "rightPowerRail", "vendorElement"]
gv_root = ET.Element("resource")
# Load the XML file
input_file = "../data/Inputs/VAR_1.xml"
output_file = "../LD/Inters/preprocess.xml"
var_output = "../data/Inters/vars.xml"




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
def main():
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    modified_xml = strip_namespace(root)
    root = ET.fromstring(modified_xml)
    # clear var_out file
    with open(var_output, 'w', encoding='utf-8') as f:
        f.write("")
    # extract global vars
    extract_global_vars(root)           
