import sys
sys.path.append("../")

from LD.Schema.Elements import Type, Variable
import xml.etree.ElementTree as ET
import os
import glob

from Logs.colorLogger import get_color_logger
logger = get_color_logger("ASSEMBLE")


BASE_XML_PATH = "../data/Base/beremiz_base2.xml"
OUTPUT_PATH = "../data/Outputs/plc.xml"
VARS_PATH = "../data/Inters/vars.xml"
POUS_PATH = ["LD/Outputs"]
# Parse the base XML
base_root = ET.parse(BASE_XML_PATH).getroot()
# Parse the vars XML
gvars_root = ET.parse(VARS_PATH).getroot()
# Insert global vars to the base XML
# First, find the <resource> tag in base XML

# TBD: not supporting multiple configurations yet
def deal_configuration(root: ET.Element) -> None:
    logger.debug("Processing configuration.")
    if root.tag != "configuration":
        logger.error(f"Root tag is {root.tag} NOT'configuration'. Failed to process configuration.")
        return
    # TBD: insert task info
    # insert global vars
    resource = root.find("resource")
    if resource is None:
        logger.error("Failed to find <resource> tag in configuration.")
        return
    for gvar in gvars_root:
        resource.append(gvar)

def deal_pous(root: ET.Element) -> None:
    if root.tag != "pous":
        logger.error(f"Root tag is {root.tag} NOT 'pous'. Failed to process pous.")
        return
    
    # Insert the pou files from POUS_PATH
    for cur_dir in POUS_PATH:
        files = glob.glob(f"{cur_dir}/T_*.xml")
        for file in files:
            logger.debug(f"Inserting {file}")
            pou_root = ET.parse(file).getroot()
            if pou_root.tag != "pou":
                logger.error(f"Root tag is {pou_root.tag} NOT 'pou'. Failed to process pou.")
                return
            root.append(pou_root)


def main():
    inst = base_root.find("instances")
    if inst is None:
        logger.error("Failed to find <instances> tag in the base XML.")
        sys.exit(1)
    configurations = inst.find("configurations")
    if configurations is None:
        logger.error("Failed to find <configurations> tag in the base XML.")
        sys.exit(1)
    for configuration in configurations:
        if configuration.tag == "configuration":
            deal_configuration(configuration)
        else:
            logger.warning(f"Unknown tag: {configuration.tag}")

    types = base_root.find("types")
    if types is None:
        logger.error("Failed to find <types> tag in the base XML.")
        sys.exit(1)
    pous = types.find("pous")
    if pous is None:
        logger.error("Failed to find <pous> tag in the base XML.")
        sys.exit(1)
    deal_pous(pous)

  # Write the output XML
    ET.ElementTree(base_root).write(OUTPUT_PATH)