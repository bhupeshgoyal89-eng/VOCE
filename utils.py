"""
Utility functions for VOCE
"""

import os
import uuid
from datetime import datetime
from typing import Optional


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique ID string
    """
    unique_part = str(uuid.uuid4())[:8].upper()
    if prefix:
        return f"{prefix}_{unique_part}"
    return unique_part


def save_uploaded_file(uploaded_file, destination_dir: str) -> Optional[str]:
    """
    Save uploaded file to destination directory
    
    Args:
        uploaded_file: Streamlit uploaded file object
        destination_dir: Directory to save file
        
    Returns:
        Path to saved file or None if failed
    """
    try:
        os.makedirs(destination_dir, exist_ok=True)
        
        file_path = os.path.join(destination_dir, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime object for display
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        return "N/A"
    
    if isinstance(dt, str):
        return dt
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to max length with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def is_valid_vendor_id(vendor_id: str) -> bool:
    """
    Validate vendor ID format
    
    Args:
        vendor_id: Vendor ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return bool(vendor_id and len(str(vendor_id).strip()) > 0)


def safe_convert_bool(value) -> bool:
    """
    Safely convert value to boolean
    
    Args:
        value: Value to convert
        
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'y', 'active']
    
    return bool(value)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted file size
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes or 0 if error
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def create_agreement_id(vendor_id: str, file_name: str) -> str:
    """
    Create agreement ID from vendor ID and filename
    
    Args:
        vendor_id: Vendor ID
        file_name: File name
        
    Returns:
        Agreement ID
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"AGR_{vendor_id}_{timestamp}"
