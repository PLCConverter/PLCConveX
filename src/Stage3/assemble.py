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
POU_CHANGE_PATH = "ST/Outputs/change.txt"
POUS_PATH = ["LD/Outputs", "ST/Outputs"]
TASK_PATH = "Task/Outputs/tasks.xml"
# Parse the base XML
base_root = ET.parse(BASE_XML_PATH).getroot()
# Parse the vars XML
gvars_root = ET.parse(VARS_PATH).getroot()
# Parse the tasks XML
tasks_root = ET.parse(TASK_PATH).getroot()
# Insert global vars to the base XML
# First, find the <resource> tag in base XML

# TBD: not supporting multiple configurations yet
def deal_configuration(root: ET.Element) -> None:
    logger.debug("Processing configuration.")
    if root.tag != "configuration":
        logger.error(f"Root tag is {root.tag} NOT'configuration'. Failed to process configuration.")
        return
    resource = root.find("resource")
    if resource is None:
        logger.error("Failed to find <resource> tag in configuration.")
        return
    # insert task info
    task_elements = tasks_root.findall("task")
    if not task_elements:
        logger.warning("No task elements found")
        # leave the default task in the base XML
    else:
        #remove the default task in the base XML
        default_task = resource.find("task")
        if default_task is not None:
            resource.remove(default_task)
        for task_element in task_elements:
            resource.append(task_element)

    # insert global vars
    for gvar in gvars_root:
        resource.append(gvar)

def deal_pous(root: ET.Element) -> None:
    if root.tag != "pous":
        logger.error(f"Root tag is {root.tag} NOT 'pous'. Failed to process pous.")
        return
    
    # read the list of pou changes separated by new line
    with open(POU_CHANGE_PATH, "r") as f:
        pou_changes = f.read().splitlines()

    # Insert the pou files from POUS_PATH
    for cur_dir in POUS_PATH:
        files = glob.glob(f"{cur_dir}/T_*.xml")
        for file in files:
            logger.debug(f"Inserting {file}")
            pou_root = ET.parse(file).getroot()
            if pou_root.tag != "pou":
                logger.error(f"Root tag is {pou_root.tag} NOT 'pou'. Failed to process pou.")
                continue
            name = pou_root.get("name")
            if name is None:
                logger.error(f"Failed to get 'name' attribute of pou.")
                continue
            if name in pou_changes:
                logger.debug(f"Changing {name}'s pouType")
                pou_root.set("pouType", "functionBlock")
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

if __name__ == "__main__":
    main()