# go through LD/Inters and LD/Outputs to delete any file that starts with "T_"

import os
import glob

from Logs.colorLogger import get_color_logger
logger = get_color_logger("ST/clean.py")

# Get the list of files in "ST/Inters" matching the pattern "T_*.xml"
def main():
    files = glob.glob("ST/Inputs/T_*.xml")
    for full_path in files:
        os.remove(full_path)
    files = glob.glob("ST/Inters/T_*.xml")
    for full_path in files:
        os.remove(full_path)
    files = glob.glob("ST/Outputs/T_*.xml")
    for full_path in files:
        os.remove(full_path)

if __name__ == "__main__":
    main()