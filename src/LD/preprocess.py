import xml.etree.ElementTree as ET

# Define the elements to be removed
# !!! WARNING: vendorElement maybe reinstated in the future !!!
GLOBAL_SLASH_LIST = ["addData", "rightPowerRail", "vendorElement"]

# Load the XML file
input_file = "./Inputs/LD_RACK_1.xml"
output_file = "./Inters/preprocess.xml"

tree = ET.parse(input_file)
root = tree.getroot()

def remove_unsupported_elements(parent):
    """Recursively remove unsupported elements from the XML tree."""
    for elem in list(parent):
        if elem.tag in GLOBAL_SLASH_LIST:
            parent.remove(elem)
        else:
            remove_unsupported_elements(elem)  # Recursively check children



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


# Remove elements
remove_unsupported_elements(root)
# Convert formalParameter attributes
convert_fp_tree(root)



# Save the modified XML to a new file without XML declaration header
tree.write(output_file, encoding="utf-8", xml_declaration=False)

print(f"Processed XML saved to {output_file}")
