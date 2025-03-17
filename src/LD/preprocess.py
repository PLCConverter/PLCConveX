import xml.etree.ElementTree as ET
import argparse

# Define the elements to be removed
# !!! WARNING: vendorElement maybe reinstated in the future !!!
GLOBAL_SLASH_LIST = ["addData", "rightPowerRail", "vendorElement"]

# Convert formalParameter attributes
FORMALPARAMETER_MAP = {
    'Out1': 'OUT',
    'Out2': 'OUT',
}

DEFAULT_INPUT = 'LD/Inputs/T_FB0.xml'
DEFAULT_OUTPUT = 'LD/Inters/preprocess.xml'

def remove_unsupported_elements(parent):
    """Recursively remove unsupported elements from the XML tree."""
    for elem in list(parent):
        if elem.tag in GLOBAL_SLASH_LIST:
            parent.remove(elem)
        else:
            remove_unsupported_elements(elem)  # Recursively check children

def convert_formal_parameter(elem: ET.Element) -> None:
    """Convert formalParameter attributes in the XML element."""
    if elem.tag == "inputVariables":
        fp_list = []
        var_list = elem.findall("variable")
        for var in var_list:
            fp = var.get("formalParameter")
            if fp is not None:
                fp_list.append(fp)
        if "In3" in fp_list:
            print("Converting formalParameter 'In3' to 'IN2', 'In2' to 'IN1'.")
            for var in var_list:
                if var.get("formalParameter") == "In2":
                    var.set("formalParameter", "IN1")
                if var.get("formalParameter") == "In3":
                    var.set("formalParameter", "IN2")
        else:
            for var in var_list:
                if var.get("formalParameter") == "In2":
                    print("Converting formalParameter 'In2' to 'IN'.")
                    var.set("formalParameter", "IN")
        return
    
    fp = elem.get("formalParameter")
    if fp is None:
        return
    if fp in FORMALPARAMETER_MAP:
        print(f"Converting formalParameter '{fp}' to '{FORMALPARAMETER_MAP[fp]}'.")
        elem.set("formalParameter", FORMALPARAMETER_MAP[fp])

def convert_fp_tree(root: ET.Element):
    """Recursively convert formalParameter attributes in the XML tree."""
    if root is None:
        return
    convert_formal_parameter(root)
    for child in list(root):
        convert_fp_tree(child)

def process_xml(input_file, output_file):
    """Process the XML file by removing elements and converting attributes."""
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    remove_unsupported_elements(root)
    convert_fp_tree(root)
    
    tree.write(output_file, encoding="utf-8", xml_declaration=False)
    print(f"Processed XML saved to {output_file}")

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
        # input like : "LD/Inputs/T_xxxx.xml"
        # generate output path like : "LD/Inters/T_xxxx_preprocess.xml"
        args.output = args.input.replace("Inputs", "Inters").replace(".xml", "_preprocess.xml")
        print(args.output)
    process_xml(args.input, args.output)

if __name__ == "__main__":
    main()

