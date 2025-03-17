import os
import sys
import subprocess
import glob

from Logs.colorLogger import get_color_logger
logger = get_color_logger("LD")


# Get the list of files in "LD/Inters" matching the pattern "T_*.xml"
files = glob.glob("LD/Inputs/T_*.xml")

# Iterate over each file found
def main():
  for full_path in files:
      # Extract just the filename (e.g., "T_xxxx.xml") from the full path
      filename = os.path.basename(full_path)
      logger.info(f"Processing {filename}")
      
      # Step 1: Call LD/preprocess.py with argument --input T_xxxx.xml
      subprocess.run([sys.executable, "LD/preprocess.py", "--input", full_path])
      
      # Step 2: Call LD/Block/test.py with argument --input T_xxxx.xml
      # path changed to "LD/Inters/T_xxxx_preprocess.xml"
      path = full_path.replace("Inputs", "Inters").replace(".xml", "_preprocess.xml")
      logger.debug(f"Calling Block/test.py with {path}")
      subprocess.run([sys.executable, "LD/Block/test.py", "--input", path])
      
      # Step 3: Call LD/Locate/test.py with argument --input T_xxxx.xml
      # path changed to "LD/Inters/T_xxxx_intermediate.xml"
      path = full_path.replace("Inputs", "Inters").replace(".xml", "_intermediate.xml")
      logger.debug(f"Calling Locate/test.py with {path}")
      subprocess.run([sys.executable, "LD/Locate/test.py", "--input", path])

