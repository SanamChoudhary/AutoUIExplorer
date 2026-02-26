"""
Terminal formatting utilities for AutoUIExplorer.

Provides ANSI color codes, colored text helpers, and a flush-safe
log function for real-time terminal output.
"""


# ANSI colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def colored(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{color}{text}{Colors.END}"


def log(message: str = ""):
    """Print with immediate flush for real-time output."""
    print(message, flush=True)
