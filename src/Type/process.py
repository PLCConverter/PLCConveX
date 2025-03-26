import re
import xml.etree.ElementTree as ET 

from Type.Schema import Struct, DataType, BaseType, DataTypes 

from Logs.colorLogger import get_color_logger
logger = get_color_logger("Type/process.py")

DEFAULT_INPUT_PATH = "Type/Inputs/types.xml"
DEFAULT_OUTPUT_PATH = "Type/Outputs/types.xml"

def process_types(root: ET.Element):

    dts_element = root.find('dataTypes')
    if dts_element is None:
        logger.warning("No dataTypes element found")
        return None
    dts = DataTypes.parse(dts_element)
    return dts

def main(input_path = DEFAULT_INPUT_PATH, output_path = DEFAULT_OUTPUT_PATH):
    tree = ET.parse(input_path)
    root = tree.getroot()
    dts = process_types(root)
    if dts is None:
        logger.warning("No dataTypes found")
        return
    tp_element = ET.Element('types')
    tp_element.append(dts.to_xml())
    # write to file
    ET.ElementTree(tp_element).write(output_path)

if __name__ == "__main__":
    main()
    
