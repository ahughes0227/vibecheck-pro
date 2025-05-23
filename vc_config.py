# vc_config.py
# Description: Configuration constants for the VC Analyzer.

"""
Configuration settings for the VibeCheck Pro application.
This module contains all the configurable parameters used throughout the application.
These settings can be modified to change the behavior of the application without changing the code.
"""

# --- Application Settings ---
APP_NAME = "VibeCheck Pro"  # The name of the application
APP_VERSION = "1.0.0"  # Current version of the application

# --- File Processing Settings ---
# Maximum number of files that can be processed at once
MAX_FILES = 100

# Maximum number of data points to process per file
# This helps prevent memory issues with very large files
MAX_DATA_POINTS = 1000000

# --- Analysis Settings ---
# Default frequency range for analysis (in Hz)
DEFAULT_FREQ_MIN = 0.1
DEFAULT_FREQ_MAX = 1000.0

# Default window size for FFT analysis (in seconds)
DEFAULT_WINDOW_SIZE = 1.0

# Default overlap between windows (as a percentage)
DEFAULT_WINDOW_OVERLAP = 0.5

# --- Plot Settings ---
# Default figure size for plots (width, height in inches)
DEFAULT_FIGURE_SIZE = (12, 8)

# Default DPI (dots per inch) for plots
DEFAULT_DPI = 300

# Default color palette for plots
DEFAULT_COLORS = [
    '#1f77b4',  # Blue
    '#ff7f0e',  # Orange
    '#2ca02c',  # Green
    '#d62728',  # Red
    '#9467bd',  # Purple
    '#8c564b',  # Brown
    '#e377c2',  # Pink
    '#7f7f7f',  # Gray
    '#bcbd22',  # Yellow
    '#17becf'   # Cyan
]

# --- PDF Report Settings ---
# Default title for PDF reports
DEFAULT_REPORT_TITLE = "VibeCheck Pro Analysis Report"

# Default author for PDF reports
DEFAULT_REPORT_AUTHOR = "VibeCheck Pro"

# Default subject for PDF reports
DEFAULT_REPORT_SUBJECT = "Vibration Analysis Report"

# --- Logging Settings ---
# Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
DEFAULT_LOG_LEVEL = "INFO"

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# --- Error Handling Settings ---
# Maximum number of retries for failed operations
MAX_RETRIES = 3

# Time to wait between retries (in seconds)
RETRY_DELAY = 1.0

# --- Performance Settings ---
# Number of worker threads for parallel processing
NUM_WORKERS = 4

# Chunk size for processing large files
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

# --- Unit Conversion ---
UMS_TO_MM_S = 1e-3  # Conversion factor from um/s to mm/s
Y_UNIT = "Velocity (mm/s RMS)"  # Y-axis unit label for plots

# --- Vibration Criteria Thresholds ---
# Values are in mm/s RMS
VC_THRESHOLDS = {
    'VC-A': 50 * UMS_TO_MM_S,
    'VC-B': 25 * UMS_TO_MM_S,
    'VC-C': 12.5 * UMS_TO_MM_S,
    'VC-D': 6.25 * UMS_TO_MM_S,
    'VC-E': 3.12 * UMS_TO_MM_S,
    'VC-F': 1.56 * UMS_TO_MM_S,
}

# --- Color Palette for Plots and PDF ---
COLOR_PALETTE = {
    'X': '#1b9e77',      # Teal
    'Y': '#d95f02',      # Orange
    'Z': '#7570b3',      # Purple
    'VC-A': '#e7298a',   # Pink
    'VC-B': '#66a61e',   # Green
    'VC-C': '#e6ab02',   # Yellow/Ochre
    'VC-D': '#a6761d',   # Brown
    'VC-E': '#666666',   # Gray
    'VC-F': '#17becf',   # Light Blue / Cyan
}

# --- Debug Configuration ---
# To use hardcoded paths for debugging vc_analyzer_main.py directly,
# uncomment and set the following variables with YOUR ACTUAL PATHS.
# When DEBUG_FILE_PATHS is not None (and the others are set),
# vc_analyzer_main.py will use these values.

# Example (replace with your actual paths):
# DEBUG_FILE_PATHS = [
# r"C:\Users\YourUserName\Desktop\TestData\test_file_01.ide",
# r"C:\Users\YourUserName\Desktop\TestData\test_file_02.ide" # Add more if needed
# ]
# DEBUG_OUTPUT_DIR = r"C:\Users\YourUserName\Desktop\TestData\DebugOutput" # Make sure this folder exists
# DEBUG_LOCATION_TOOL_NAME = "My Debug Session"

DEBUG_FILE_PATHS = ["Aircraft_Vibration.IDE"] # Path to your test file
DEBUG_OUTPUT_DIR = "debug_output" # Ensure this directory exists or can be created
DEBUG_LOCATION_TOOL_NAME = "Debug Run"
# --- END DEBUG CONFIGURATION ---