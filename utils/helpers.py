"""
Helper utilities and functions
"""

import re
import os
from pathlib import Path
from typing import Union


def format_size(size_bytes: int) -> str:
    """Format byte size into human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1
    
    return f"{size:.1f}{size_names[size_index]}"


def parse_size(size_str: str) -> int:
    """Parse human readable size string to bytes"""
    size_str = size_str.upper().strip()
    
    # Extract number and unit
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]?B?)$', size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")
    
    number = float(match.group(1))
    unit = match.group(2) or 'B'
    
    # Convert to bytes
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4
    }
    
    if unit not in multipliers:
        raise ValueError(f"Unknown size unit: {unit}")
    
    return int(number * multipliers[unit])


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem storage"""
    # Remove or replace invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext
    
    # Ensure it's not empty
    if not filename:
        filename = "untitled"
    
    return filename


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_extension(url: str) -> str:
    """Extract file extension from URL"""
    path = Path(url.split('?')[0])  # Remove query parameters
    return path.suffix.lower()


def is_url_valid(url: str) -> bool:
    """Check if URL format is valid"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None


def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate string to maximum length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."