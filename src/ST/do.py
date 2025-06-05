import os
import sys
import subprocess
import glob

from Logs.colorLogger import get_color_logger
logger = get_color_logger("ST")


# Get the list of files in "ST/Inters" matching the pattern "T_*.xml"
files = glob.glob("ST/Inputs/T_*.xml")
# files to be created if not exist
CHANGE_PATH = "ST/Outputs/change.txt"


# Iterate over each file found
def main():
  with open(CHANGE_PATH, "w") as f:
    f.write("")

  for full_path in files:
      # Extract just the filename (e.g., "T_xxxx.xml") from the full path
      filename = os.path.basename(full_path)
      logger.info(f"Processing {filename}")
      
      # Step 1: Call ST/preprocess.py with argument --input T_xxxx.xml
      logger.debug(f"Calling ST/preprocess.py {full_path}")
      subprocess.run([sys.executable, "ST/preprocess.py", "--input", full_path])
      
      path = full_path.replace("Inputs", "Inters").replace(".xml", "_preprocess.xml")
      logger.debug(f"Calling syntax.py with {path}")
      subprocess.run([sys.executable, "ST/syntax.py", "--input", path])

if __name__ == "__main__":
    main()

