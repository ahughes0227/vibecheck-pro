# VibeCheck Pro

VibeCheck Pro is a cross‑platform vibration analysis suite combining an Electron user interface with a Python back end. It allows engineers and researchers to inspect `.IDE` sensor files, visualize vibration levels and generate detailed interactive reports. Use it for predictive maintenance, quality control or any workflow that requires quick insight into vibration data.

---

## Features

* **Cross‑platform:** runs on Windows, macOS and Linux
* **Real‑time analysis:** immediately process uploaded sensor files
* **Interactive HTML reports:** Plotly graphs with zoom/pan capabilities
* **Modern UI:** drag‑and‑drop file upload with a clean layout
* **Python‑powered:** uses scientific libraries for accurate calculations
* **Auto‑update:** built‑in updater via GitHub releases

## Tech Stack

* **Frontend:** Electron with HTML/CSS/JavaScript
* **Backend:** Flask (Python)
* **Data processing:** NumPy, SciPy, pandas, endaq
* **Reporting:** Plotly, ReportLab

## Directory Structure

```
├── vibecheck/            # Python package with analysis code
│   ├── flask_server.py   # Flask API for file upload/analysis
│   ├── vc_analyzer_endaq.py
│   ├── vc_plot_sensor_data.py
│   ├── vc_generate_pdf.py
│   ├── vc_config.py
│   └── vc_utils.py
├── assets/               # Application icons and logos
├── main.js               # Electron entry point
├── index.html            # Electron UI
├── tests/                # Pytest suite with sample IDE file
└── user_guide.html       # Step‑by‑step usage instructions
```

## Installation

1. **Download the latest release** from the [GitHub Releases page](https://github.com/AHughes0227/vibecheck-pro/releases).
2. **Run the installer** for your platform (Windows, macOS or Linux).
3. **Launch VibeCheck Pro** and start analyzing data.

For development, clone the repo and install the Node.js and Python dependencies:

```bash
git clone https://github.com/AHughes0227/vibecheck-pro.git
cd vibecheck-pro
npm install
pip install -r requirements.txt
```

## Usage

1. Start the application (or run `npm run dev` during development).
2. Drag and drop an `.IDE` file or choose **Add File(s)** in the interface.
3. View the generated interactive report in your browser and optionally export a PDF.
4. Check `user_guide.html` for a more detailed walkthrough of features.

## Build a Release

Create a production-ready bundle and generate a clean `release/` directory with:

```bash
npm run release -- --zip
```

This runs the Electron build, strips development files and packages the output as `release.zip`.

## Testing

Run the Python test suite with `pytest`:

```bash
pytest -q
```

The tests cover HTML report creation, Flask API endpoints and VC threshold calculations. A sample IDE file is included under `tests/`.

## Contributing

Contributions and bug reports are welcome! Feel free to open an issue or submit a pull request if you have improvements or new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for full details.
