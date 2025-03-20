import os
import sys
import subprocess
import glob

from Logs.colorLogger import get_color_logger
logger = get_color_logger("stage3")

def main():

    # Step 1: Call Stage3/assemble.py
    logger.debug(f"Stage3/assemble.py")
    subprocess.run([sys.executable, "Stage3/assemble.py"])
    
    # Step 2: Call Stage3/postprocess.py 
    logger.debug(f"Stage3/postprocess.py")
    subprocess.run([sys.executable, "Stage3/postprocess.py"])


