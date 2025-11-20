"""
Utility functions for the Solidity scanner.
"""

import logging
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_solidity_files(path: str) -> List[Path]:
    """
    Recursively find all .sol files in the given path.

    Args:
        path: Directory path or file path to search

    Returns:
        List of Path objects for .sol files
    """
    path_obj = Path(path)
    sol_files = []

    if path_obj.is_file() and path_obj.suffix == ".sol":
        sol_files.append(path_obj)
    elif path_obj.is_dir():
        sol_files.extend(path_obj.rglob("*.sol"))
    else:
        logger.warning(f"Path {path} is not a valid file or directory")

    return sol_files


def read_file_content(file_path: Path) -> Optional[str]:
    """
    Read content from a file.

    Args:
        file_path: Path to the file

    Returns:
        File content as string, or None if error

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read due to permissions
        UnicodeDecodeError: If file cannot be decoded as UTF-8
    """
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Check file size (prevent memory exhaustion)
        max_size = 10 * 1024 * 1024  # 10MB limit
        if file_path.stat().st_size > max_size:
            logger.warning(f"File {file_path} exceeds size limit ({max_size} bytes)")
            raise ValueError(f"File too large: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            logger.debug(f"Successfully read {len(content)} characters from {file_path}")
            return content

    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Unable to decode file as UTF-8: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading file {file_path}: {e}", exc_info=True)
        raise


def get_severity_color(severity: str) -> str:
    """
    Get ANSI color code for severity level.

    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)

    Returns:
        ANSI color code string
    """
    colors = {
        "CRITICAL": "\033[91m",  # Red
        "HIGH": "\033[95m",  # Magenta
        "MEDIUM": "\033[93m",  # Yellow
        "LOW": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
    }
    reset = "\033[0m"
    return colors.get(severity.upper(), "") + severity + reset


def format_code_snippet(lines: List[str], line_number: int, context: int = 3) -> str:
    """
    Format code snippet with line numbers for display.

    Args:
        lines: List of code lines
        line_number: The line number to highlight (1-indexed)
        context: Number of lines before/after to include

    Returns:
        Formatted code snippet string
    """
    start = max(0, line_number - context - 1)
    end = min(len(lines), line_number + context)

    snippet_lines = []
    for i in range(start, end):
        marker = ">>> " if i == line_number - 1 else "    "
        snippet_lines.append(f"{marker}{i + 1:4d} | {lines[i]}")

    return "\n".join(snippet_lines)
