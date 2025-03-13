import logging

# ANSI escape codes for colors
COLORS = {
    'DEBUG': '\033[34m',    # Blue
    'INFO': '\033[32m',     # Green
    'WARNING': '\033[33m',  # Yellow
    'ERROR': '\033[31m',    # Red
    'CRITICAL': '\033[1;31m' # Bold Red
}
RESET = '\033[0m'           # Reset to default color

class ColorFormatter(logging.Formatter):
    """A custom formatter that adds color to log level names."""
    def __init__(self, fmt=None, datefmt=None, style='%'):
        # Use a default format if none is provided
        if fmt is None:
            fmt = '%(levelname)s: %(message)s'
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        """Override format to add color to the levelname."""
        levelname = record.levelname
        if levelname in COLORS:
            # Wrap the levelname with color codes
            record.levelname = COLORS[levelname] + levelname + RESET
        return super().format(record)

def get_color_logger(name='colorLogger', level=logging.DEBUG):
    """
    Returns a logger with colored output.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())
    logger.addHandler(console_handler)
        
    return logger