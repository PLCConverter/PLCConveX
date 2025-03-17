# go through LD/Inters and LD/Outputs to delete any file that starts with "T_"

import os
import glob

from Logs.colorLogger import get_color_logger
logger = get_color_logger("LD/clean.py")

# Get the list of files in "LD/Inters" matching the pattern "T_*.xml"
def main():
    files = glob.glob("LD/Inputs/T_*.xml")
    for full_path in files:
        os.remove(full_path)
    files = glob.glob("LD/Inters/T_*.xml")
    for full_path in files:
        os.remove(full_path)
    files = glob.glob("LD/Outputs/T_*.xml")
    for full_path in files:
        os.remove(full_path)

if __name__ == "__main__":
    main()