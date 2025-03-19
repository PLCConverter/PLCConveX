import re

# --- Recognition Functions ---
from Logs.colorLogger import get_color_logger
logger = get_color_logger("TOKEN")

def recognize_integer_literal(text):
    """
    Recognize integer literals, including type-prefixed (e.g., INT#123), base-specific (e.g., 2#1010), 
    and plain integers (e.g., 123 or +123).
    
    Args:
        text (str): The input text to check for an integer literal.
    
    Returns:
        tuple: A tuple ("integer", matched_string) if a match is found at the start, else None.
    """
    pattern = r'(?:SINT|INT|DINT|LINT|USINT|UINT|UDINT|ULINT)#[+-]?\d+|2#[0-1]+|8#[0-7]+|16#[0-9A-Fa-f]+|[+-]?\d+'
    match = re.match(pattern, text)
    if match:
        return ("integer", match.group(0))
    return None

def recognize_real_literal(text):
    """
    Recognize real literals, including type-prefixed (e.g., REAL#3.14) and plain reals (e.g., 3.14 or -0.5).
    
    Args:
        text (str): The input text to check for a real literal.
    
    Returns:
        tuple: A tuple ("real", matched_string) if a match is found at the start, else None.
    """
    pattern = r'(?:REAL|LREAL)#[+-]?\d+\.\d+|[+-]?\d+\.\d+'
    match = re.match(pattern, text)
    if match:
        return ("real", match.group(0))
    return None

def recognize_character_string(text):
    """
    Recognize character strings, including single-quoted (e.g., 'hello'), double-quoted (e.g., "world"), 
    and double-byte strings (e.g., $"hello").
    
    Args:
        text (str): The input text to check for a character string.
    
    Returns:
        tuple: A tuple ("string", matched_string) if a match is found at the start, else None.
    """
    pattern = r"'[^']*'|\"[^\"]*\"|\$\"[^\"]*\""
    match = re.match(pattern, text)
    if match:
        return ("string", match.group(0))
    return None

def recognize_time_literal(text):
    """
    Recognize time literals, including duration (e.g., T#1h30m), time of day (e.g., TIME_OF_DAY#12:30:00), 
    and date (e.g., DATE#2023-10-15).
    
    Args:
        text (str): The input text to check for a time literal.
    
    Returns:
        tuple: A tuple ("time", matched_string) if a match is found at the start, else None.
    """
    pattern = r'(?:T|TIME)#[+-]?[^\s]*[mMsShHdD]|TIME_OF_DAY#\d{2}:\d{2}:\d{2}(?:\.\d+)?|DATE#\d{4}-\d{2}-\d{2}'
    match = re.match(pattern, text)
    if match:
        return ("time", match.group(0))
    return None

def recognize_boolean_literal(text):
    """
    Recognize boolean literals, optionally prefixed with BOOL# (e.g., BOOL#TRUE or TRUE).
    
    Args:
        text (str): The input text to check for a boolean literal.
    
    Returns:
        tuple: A tuple ("boolean", matched_string) if a match is found at the start, else None.
    """
    pattern = r'(?:BOOL#)?(?:TRUE|FALSE)'
    match = re.match(pattern, text)
    if match:
        return ("boolean", match.group(0))
    return None

# --- Main Tokenization Function ---

def tokenize_literals(text: str) -> bool:
    """
    Tokenize the input text to recognize and print various literals in sequence.
    
    Args:
        text (str): The input text containing literals to be tokenized.
    """
    # List of recognizer functions in order of precedence
    recognizers = [
        recognize_time_literal,      # Specific formats like T# or DATE#
        recognize_character_string,  # Quoted strings
        recognize_real_literal,      # Reals before integers to catch decimal points
        recognize_integer_literal,   # Integers after reals to avoid partial matches
        recognize_boolean_literal    # Keywords TRUE/FALSE
    ]
    
    # only one word, judege if it's a literal
    for word in text.split():
        for recognizer in recognizers:
            result = recognizer(word)
            if result:
                logger.debug(f"{result[0]} literal: {result[1]}")
                return True
    logger.debug("No literal found.")
    return False

# --- Test the Code ---

if __name__ == "__main__":
    # Sample input containing various literals separated by spaces
    input_code = "INT#123 REAL#3.14 'hello' T#1h30m TRUE 456 TIME#1.5S"
    print("Tokenizing input:", input_code)
    print("-" * 40)
    tokenize_literals(input_code)