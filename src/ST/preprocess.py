import sys
sys.path.append('..')

import re
import argparse

from Logs.colorLogger import get_color_logger
logger = get_color_logger("ST_Preprocess")


DEFAULT_INPUT = 'ST/Inputs/fuck.xml'
DEFAULT_OUTPUT = 'ST/Inters/T_test.xml'

def process_xml(input_file, output_file):
    # Reads input file, converts single-line // comments to Beremiz-style (* ... *),
    # and writes the modified content to the output file.
    # This function assumes input_file exists and output_file path is writable.

    def comment_replacer(match_obj):
        # Helper function for re.sub.
        # Takes a match object from a regex finding "//" comments.
        # Group 1 is the content before "//".
        # Group 2 is the comment text after "//".
        # Returns the string formatted as "content_before(* comment_text_trimmed *)".
        code_part = match_obj.group(1)
        comment_text = match_obj.group(2)
        return f"{code_part}(* {comment_text.strip()} *)"

    with open(input_file, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    processed_lines = []
    for line in lines:
        original_line_content = line.rstrip('\n\r') # Remove trailing newline/CR for processing
        
        # Regex to find and capture parts of a // style comment:
        # (.*?)  -> Group 1: Any characters before // (non-greedy).
        # //     -> Matches the literal // comment marker.
        # (.*)   -> Group 2: Any characters after // until the end of the line.
        modified_line_content = re.sub(
            r'(.*?)//(.*)', 
            comment_replacer, 
            original_line_content
        )
        processed_lines.append(modified_line_content + '\n') # Add newline back

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.writelines(processed_lines)
    
    logger.info(f"Comment conversion complete for '{input_file}'. Output saved to '{output_file}'.")
    

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
        args.output = args.input.replace("Inputs", "Inters").replace(".xml", "_preprocess.xml")
        logger.debug(f"Output file path: {args.output}")
    process_xml(args.input, args.output)

if __name__ == "__main__":
    main()