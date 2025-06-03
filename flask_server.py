import os
import sys
import logging
import tempfile
import webbrowser
import threading
import time
from pathlib import Path
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
from vc_analyzer_endaq import analyze_endaq
from vc_plot_sensor_data import create_vc_plots_plotly

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Constants
ALLOWED_EXTENSIONS = {'ide', 'IDE'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def launch_chrome(url):
    """Launch Chrome with the given URL."""
    try:
        # Try to use Chrome specifically
        chrome_path = None
        if sys.platform == 'win32':
            chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
        elif sys.platform == 'darwin':
            chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
        elif sys.platform.startswith('linux'):
            chrome_path = '/usr/bin/google-chrome %s'

        if chrome_path:
            webbrowser.get(chrome_path).open(url)
        else:
            # Fallback to default browser
            webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to launch Chrome: {e}")
        # Fallback to default browser
        webbrowser.open(url)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze IDE file and return HTML report."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Please select an IDE file."}), 400

        # Create a secure temporary directory
        temp_dir = tempfile.mkdtemp(prefix='vibecheck_')
        try:
            # Save uploaded file
            file_path = os.path.join(temp_dir, secure_filename(file.filename))
            file.save(file_path)
            logger.info(f"File saved to: {file_path}")
            
            # Generate HTML report
            html_path = os.path.join(temp_dir, 'report.html')

            if not create_vc_plots_plotly(file_path, html_path):
                return jsonify({"error": "Failed to generate report"}), 500

            return send_file(html_path, mimetype='text/html')

        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            logger.error("Traceback:", exc_info=True)
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        logger.error(f"Error in request handling: {str(e)}")
        logger.error("Traceback:", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/view/<path:filename>')
def view_report(filename):
    """Serve the HTML report."""
    try:
        # Find the report in the most recent temp directory
        temp_dirs = sorted(
            [d for d in Path(tempfile.gettempdir()).glob('vibecheck_*')],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not temp_dirs:
            return "Report not found", 404
            
        report_path = temp_dirs[0] / filename
        if not report_path.exists():
            return "Report not found", 404
            
        return send_file(str(report_path), mimetype='text/html')
        
    except Exception as e:
        logger.error(f"Error serving report: {e}")
        return str(e), 500

def cleanup_old_reports():
    """Clean up old report directories."""
    try:
        temp_dirs = Path(tempfile.gettempdir()).glob('vibecheck_*')
        for d in temp_dirs:
            if (time.time() - d.stat().st_mtime) > 3600:  # 1 hour old
                try:
                    import shutil
                    shutil.rmtree(d)
                except:
                    pass
    except:
        pass

if __name__ == '__main__':
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_reports, daemon=True)
    cleanup_thread.start()
    
    # Start Flask server
    app.run(port=5001, debug=False) 