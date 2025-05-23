# vc_utils.py
# Description: Utility functions for the VC Analyzer.

import datetime as dt
import os
import re
import traceback
import sys
import tempfile
import shutil
from pathlib import Path

# --- Define AppName for consistency (matches vc_analyzer_main.py) ---
APP_NAME = "VibeCheckPro"

# File size limits
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
MAX_TOTAL_FILES_SIZE = 5 * 1024 * 1024 * 1024  # 5GB

# Cache for file sizes to avoid repeated checks
_file_size_cache = {}

def validate_file_size(file_path):
    """Validate if a file is within size limits."""
    try:
        # Check cache first
        if file_path in _file_size_cache:
            size = _file_size_cache[file_path]
        else:
            size = os.path.getsize(file_path)
            _file_size_cache[file_path] = size
            
        if size > MAX_FILE_SIZE:
            return False, f"File exceeds maximum size of 1GB: {os.path.basename(file_path)}"
        return True, size
    except (OSError, IOError) as e:
        return False, f"Error accessing file: {str(e)}"

def validate_files_size(file_paths):
    """Validate if total size of files is within limits."""
    total_size = 0
    for file_path in file_paths:
        is_valid, result = validate_file_size(file_path)
        if not is_valid:
            return False, result
        total_size += result
    
    if total_size > MAX_TOTAL_FILES_SIZE:
        return False, f"Total size of files exceeds maximum limit of 5GB"
    return True, total_size

def clear_file_size_cache():
    """Clear the file size cache."""
    global _file_size_cache
    _file_size_cache.clear()

# Global variable to store the temporary log file path
_temp_log_file = None

def _get_temp_log_file():
    """Get or create the temporary log file path."""
    global _temp_log_file
    if _temp_log_file is None:
        fd, path = tempfile.mkstemp(suffix='.txt', prefix='vibecheck_temp_')
        os.close(fd)
        _temp_log_file = path
    return _temp_log_file

def _write_to_temp_log(message, level="INFO"):
    """Write a message to the temporary log file."""
    try:
        log_file = _get_temp_log_file()
        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception as e:
        print(f"Failed to write to temp log: {str(e)}")

def save_temp_log_to_desktop():
    """Save the temporary log file to the desktop."""
    try:
        if _temp_log_file and os.path.exists(_temp_log_file):
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            final_path = os.path.join(desktop_path, "vibecheck_error.txt")
            
            # Read the temp file content
            with open(_temp_log_file, 'r') as f:
                content = f.read()
            
            # Write to desktop with additional formatting
            with open(final_path, 'w') as f:
                f.write(f"{'='*50}\n")
                f.write(f"VibeCheck Pro Error Report\n")
                f.write(f"{'='*50}\n\n")
                f.write(content)
                f.write(f"\n{'='*50}\n")
            
            # Clean up temp file
            os.remove(_temp_log_file)
            return final_path
    except Exception as e:
        print(f"Failed to save log to desktop: {str(e)}")
        return None

def cleanup_temp_log():
    """Clean up the temporary log file if it exists."""
    global _temp_log_file
    try:
        if _temp_log_file and os.path.exists(_temp_log_file):
            os.remove(_temp_log_file)
            _temp_log_file = None
    except Exception as e:
        print(f"Failed to cleanup temp log: {str(e)}")

def _default_status_callback(message_type, message, detail=None, progress=None):
    """Default callback for status updates (prints to console)."""
    log_msg = f"[{message_type.upper()}] {message}"
    if detail:
        log_msg += f" (Detail: {detail})"
    if progress is not None:
        log_msg += f" [Progress: {progress*100:.0f}%]"
    print(log_msg)

def extract_datetime_from_filename(filename):
    """
    Extracts datetime object from filename using various common patterns.

    Args:
        filename (str): The base filename or full path.

    Returns:
        datetime.datetime or None: The extracted datetime object, or None if no pattern matches.
    """
    patterns = [
        r"(\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2})",  # YYYYMMDD_HHMMSS
        r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})",  # YYYY-MM-DD_HH-MM-SS
        r"(\d{8}[_]?\d{6})",  # YYYYMMDD_HHMMSS (optional underscore)
        r"(\d{14})",  # YYYYMMDDHHMMSS (no separator)
        r"(\d{8})"  # YYYYMMDD (only date)
    ]
    base_filename = os.path.basename(filename)

    for pattern in patterns:
        match = re.search(pattern, base_filename)
        if match:
            dt_str_raw = match.group(1)
            dt_str_cleaned = dt_str_raw.replace('-', '').replace('_', '')
            try:
                if len(dt_str_cleaned) == 14:
                    return dt.datetime.strptime(dt_str_cleaned, "%Y%m%d%H%M%S")
                elif len(dt_str_cleaned) == 8:
                    return dt.datetime.strptime(dt_str_cleaned, "%Y%m%d")
            except ValueError:
                # If parsing fails for this pattern, continue to the next pattern
                continue
    return None # Return None if no pattern matches

def log_error_to_file(error_message, traceback_str, error_type, program_state=None):
    """Logs an error to the temporary log file."""
    try:
        log_file = _get_temp_log_file()
        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, "a") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Error Type: {error_type}\n")
            f.write(f"Error Message: {error_message}\n")
            
            if program_state:
                f.write("\nProgram State:\n")
                f.write(f"Start Time: {program_state.get('start_time', 'N/A')}\n")
                f.write(f"Error Time: {program_state.get('error_time', 'N/A')}\n")
                f.write(f"Input Files: {', '.join(program_state.get('input_files', []))}\n")
                f.write(f"Output Directory: {program_state.get('output_dir', 'N/A')}\n")
                f.write(f"Location/Tool: {program_state.get('location_tool', 'N/A')}\n")
                
                f.write("\nProgress Messages:\n")
                for msg in program_state.get('progress_messages', []):
                    f.write(f"[{msg['timestamp']}] {msg['type']}: {msg['message']}")
                    if msg['detail']:
                        f.write(f" (Detail: {msg['detail']})")
                    if msg['progress'] is not None:
                        f.write(f" [Progress: {msg['progress']*100:.0f}%]")
                    f.write("\n")
            
            f.write(f"\nTraceback:\n{traceback_str}\n")
            f.write(f"{'='*50}\n")
            
        return log_file
    except Exception as e:
        print(f"Failed to write error log: {str(e)}")
        return None

def resource_path(relative_path):
    """
    Get the absolute path to a resource file.
    This function helps find files whether the app is running as a script or as a compiled executable.
    
    Args:
        relative_path (str): The path to the resource file relative to the application root
    
    Returns:
        str: The absolute path to the resource file
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_temp_log():
    """
    Create a temporary log file for storing error information.
    
    Returns:
        str: Path to the created temporary log file
    """
    global _temp_log_file
    try:
        # Create a temporary file that will be automatically deleted when closed
        temp_dir = tempfile.gettempdir()
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        _temp_log_file = os.path.join(temp_dir, f"vibecheck_temp_log_{timestamp}.txt")
        
        # Create the file and write initial information
        with open(_temp_log_file, 'w', encoding='utf-8') as f:
            f.write(f"VibeCheck Pro Temporary Log\n")
            f.write(f"Created: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
        return _temp_log_file
    except Exception as e:
        print(f"Error creating temporary log: {str(e)}")
        return None

def cleanup_temp_log():
    """
    Remove the temporary log file if it exists.
    This should be called when the application closes or when starting a new analysis.
    """
    global _temp_log_file
    if _temp_log_file and os.path.exists(_temp_log_file):
        try:
            os.remove(_temp_log_file)
            _temp_log_file = None
        except Exception as e:
            print(f"Error removing temporary log: {str(e)}")

def save_temp_log_to_desktop():
    """
    Save the temporary log file to the user's desktop.
    This is used when an error occurs and the user wants to save the error information.
    
    Returns:
        str: Path to the saved log file, or None if the operation failed
    """
    global _temp_log_file
    if not _temp_log_file or not os.path.exists(_temp_log_file):
        return None
        
    try:
        # Get desktop path
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_path):
            return None
            
        # Create the destination file path
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(desktop_path, f"vibecheck_error_{timestamp}.txt")
        
        # Copy the file
        shutil.copy2(_temp_log_file, dest_path)
        return dest_path
    except Exception as e:
        print(f"Error saving temporary log to desktop: {str(e)}")
        return None