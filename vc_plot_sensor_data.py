import os
import argparse
import sys
import numpy as np
import pandas as pd
import tempfile
import logging
import shutil
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Imports – ensure your local helper + config modules are available
# -----------------------------------------------------------------------------
try:
    from vc_analyzer_endaq import analyze_endaq
    from vc_config import (
        VC_THRESHOLDS,
        COLOR_PALETTE,
        DEFAULT_DPI,          # dots‑per‑inch for pixel conversion
    )
    import plotly.graph_objects as go
    import plotly
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    logger.error("Make sure vc_analyzer_endaq.py, vc_config.py, and the 'plotly' + 'kaleido' libs are installed.")
    sys.exit(1)

# -----------------------------------------------------------------------------
# Helper utilities
# -----------------------------------------------------------------------------

def get_color(name: str, fallback: str = "black") -> str:
    """Fetch a colour from COLOR_PALETTE or fall back."""
    if isinstance(globals().get("COLOR_PALETTE"), dict):
        return COLOR_PALETTE.get(name, fallback)
    return fallback

def check_write_permission(path: str) -> bool:
    """Check if we have write permission to the directory."""
    try:
        test_file = os.path.join(path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except (IOError, OSError):
        return False

def ensure_directory_exists(path: str) -> bool:
    """Create directory if it doesn't exist, with permission checks."""
    try:
        os.makedirs(path, exist_ok=True)
        return check_write_permission(path)
    except (IOError, OSError) as e:
        logger.error(f"Failed to create/access directory {path}: {e}")
        return False

def safe_write_file(filepath: str, content: str) -> bool:
    """Safely write content to a file with error handling."""
    try:
        # Ensure parent directory exists and is writable
        parent_dir = os.path.dirname(filepath)
        if not ensure_directory_exists(parent_dir):
            logger.error(f"No write permission for directory: {parent_dir}")
            return False

        # Write to temporary file first
        temp_file = f"{filepath}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # If successful, rename to target file
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(temp_file, filepath)
        return True
    except Exception as e:
        logger.error(f"Failed to write file {filepath}: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False

# Figure sizing – 10 in wide (good for US‑letter / A4 print margins)
TARGET_WIDTH_IN = 10.0
DPI = DEFAULT_DPI if "DEFAULT_DPI" in globals() else 96
FIGURE_WIDTH_PX = int(TARGET_WIDTH_IN * DPI)

# Shared temporary directory for plots
TEMP_PLOT_DIR_NAME = "VibeCheckPro_Plots_Temp"

# Annotation positioning constants
LABEL_YSHIFT_PX = 0.5       # vertical gap below dashed line (in pixels)
LABEL_X_POS = 99          # place labels inside 1‑100 Hz plot range

# -----------------------------------------------------------------------------
# Core plotting routine
# -----------------------------------------------------------------------------

def create_vc_plots_plotly(ide_path: str, html_out: str) -> bool:
    """
    Analyze an enDAQ .IDE file and generate interactive VC‑curve plots.
    Returns True if successful, False otherwise.
    """
    if not os.path.exists(ide_path):
        logger.error(f"IDE file not found: {ide_path}")
        return False

    # ── 1. Extract sensor data ────────────────────────────────────────────────
    try:
        raw = analyze_endaq(ide_path)
        logger.info(f"Analyzer output type: {type(raw)}")
        if isinstance(raw, tuple):
            for i, df in enumerate(raw):
                logger.info(f"Sensor {i} DataFrame shape: {getattr(df, 'shape', None)}")
                logger.info(f"Sensor {i} DataFrame head:\n{getattr(df, 'head', lambda: None)()}")
        elif raw is not None:
            logger.info(f"Single DataFrame shape: {getattr(raw, 'shape', None)}")
            logger.info(f"Single DataFrame head:\n{getattr(raw, 'head', lambda: None)()}")
    except Exception as exc:
        logger.error(f"❌ Failed to analyse {ide_path}: {exc}")
        return False

    sensors: list[dict] = []
    if isinstance(raw, tuple):  # expected (25 G, 40 G)
        if raw and raw[0] is not None:
            sensors.append({"name": "25G Sensor", "df": raw[0]})
        if len(raw) > 1 and raw[1] is not None:
            sensors.append({"name": "40G Sensor", "df": raw[1]})
    elif raw is not None:
        sensors.append({"name": "25G Sensor", "df": raw})

    if not sensors:
        logger.error("No usable sensor data found.")
        return False

    # ── 2. Build Plotly figures ───────────────────────────────────────────────
    figs: list[go.Figure] = []

    for s in sensors:
        name, df = s["name"], s["df"]
        if df is None or df.empty:
            logger.warning(f"Skipping empty dataframe for {name}")
            continue

        positives = [v for v in VC_THRESHOLDS.values() if v > 0]
        for ax in ("X", "Y", "Z"):
            cols = [c for c in df.columns if c.startswith(ax)]
            if cols:
                positives.extend(df[cols[0]].to_numpy())
        if not positives:
            logger.warning(f"No positive values found for {name}")
            continue
        ymin = max(min(positives) * 0.5, 1e-4)
        ymax = max(positives) * 1.1
        y_range_log = [np.log10(ymin), np.log10(ymax)]

        for ax in ("X", "Y", "Z"):
            cols = [c for c in df.columns if c.startswith(ax)]
            if not cols:
                continue
            freqs = df.index.to_numpy()
            vel_mm_s = df[cols[0]].to_numpy()
            if len(freqs) == 0 or len(vel_mm_s) == 0:
                logger.warning(f"No data points for {name} - {ax}")
                continue
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=freqs,
                    y=vel_mm_s,
                    mode="lines",
                    name=f"Measured ({ax})",
                    line=dict(color=get_color(ax, "#1f77b4"), width=2, shape="spline", smoothing=0.7),
                    hoverinfo="x+y",
                )
            )
            for vc_name, vc_val in VC_THRESHOLDS.items():
                fig.add_hline(y=vc_val, line_dash="dash", line_color=get_color(vc_name, "grey"), line_width=1.5)
                fig.add_annotation(
                    x=LABEL_X_POS,
                    y=np.log10(vc_val),
                    xref="x",
                    yref="y",
                    text=f"{vc_name} ({vc_val:.3f} mm/s)",
                    showarrow=False,
                    xanchor="right",
                    yanchor="top",
                    yshift=-LABEL_YSHIFT_PX,
                    font=dict(size=10, color=get_color(vc_name, "#444")),
                    bgcolor="rgba(255,255,255,0)",
                    align="right",
                )
            if vel_mm_s.size:
                idx_peak = int(np.argmax(vel_mm_s))
                peak_freq, peak_val = freqs[idx_peak], vel_mm_s[idx_peak]
                fig.add_annotation(
                    x=peak_freq,
                    y=peak_val,
                    text=f"Peak: {peak_val:.3f} mm/s @ {peak_freq:.2f} Hz",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1.5,
                    ax=0,
                    ay=-40,
                    font=dict(size=10),
                    bordercolor="black",
                    borderwidth=0.5,
                    borderpad=2,
                    bgcolor="rgba(255,255,255,0.1)",
                )
            fig.update_layout(
                title_text=f"VC Curve – {name} – {ax}-Axis",
                title_x=0.5,
                width=FIGURE_WIDTH_PX,
                xaxis_title="Frequency (Hz)",
                yaxis_title="RMS Velocity (mm/s) – Log Scale",
                xaxis=dict(range=[1, 100], tickmode="linear", dtick=10),
                yaxis=dict(type="log", range=y_range_log),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor="white",
                margin=dict(l=50, r=10, b=80, t=100, pad=4),
                font=dict(size=20),
                title_font=dict(size=24),
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="LightGray", tickfont=dict(size=18))
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGray", tickfont=dict(size=18))
            figs.append(fig)
            logger.info(f"✓ Generated figure: {name} – {ax}")

            # Save a PNG snapshot for PDF reports
            try:
                img_dir = os.path.join(tempfile.gettempdir(), TEMP_PLOT_DIR_NAME)
                os.makedirs(img_dir, exist_ok=True)
                stem = os.path.splitext(os.path.basename(ide_path))[0]
                safe_name = name.replace(" ", "_")
                png_path = os.path.join(img_dir, f"{stem}_{safe_name}_{ax}.png")
                fig.write_image(png_path, width=FIGURE_WIDTH_PX, height=600)
            except Exception as e:
                logger.warning(f"Failed to write PNG for {name}-{ax}: {e}")

    if not figs:
        logger.error("No figures were generated. Check sensor data and processing.")
        return False

    # ── 3. Write HTML report ───────────────────────────────────────────────────
    try:
        # Get the embedded Plotly JS
        plotly_js = go.Figure().to_html(include_plotlyjs=True, full_html=False)
        plotly_js = plotly_js.split('<script type="text/javascript">')[1].split('</script>')[0]

        # Generate HTML parts for each figure
        parts = []
        for i, fig in enumerate(figs):
            fig_json = json.dumps(fig.to_dict(), cls=plotly.utils.PlotlyJSONEncoder)
            parts.append(f"""
            <div id="plot{i}" style="width:100%;height:600px;"></div>
            <script type="text/javascript">
                var plot{i} = {fig_json};
                Plotly.newPlot('plot{i}', plot{i}.data, plot{i}.layout);
            </script>
            """)

        # Combine everything into the final HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Vibration Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0 1rem;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .plot-container {{
            margin-bottom: 40px;
            padding: 20px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
    </style>
    <script type="text/javascript">
        {plotly_js}
    </script>
</head>
<body>
    <div class="container">
    <h1>Vibration Analysis Report – {os.path.basename(ide_path)}</h1>
    {''.join(parts)}
    </div>
</body>
</html>"""

        # Safely write the file
        if not safe_write_file(html_out, html):
            logger.error(f"Failed to write HTML report to {html_out}")
            return False

        logger.info(f"HTML Report saved to: {html_out}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}")
        return False

# -----------------------------------------------------------------------------
# CLI wrapper
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate VC‑curve plots from an enDAQ .IDE file.")
    parser.add_argument("ide_file", help="Path to the .IDE input file")
    parser.add_argument("-o", "--output", help="Output HTML path (default: next to IDE)")
    args = parser.parse_args()

    if not os.path.isfile(args.ide_file):
        print("IDE file not found", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        html_out = args.output
    else:
        html_out = os.path.splitext(args.ide_file)[0] + "_report.html"

    # Generate report
    if create_vc_plots_plotly(args.ide_file, html_out):
        print(f"Report generated successfully: {html_out}")
        sys.exit(0)
    else:
        print("Failed to generate report", file=sys.stderr)
        sys.exit(1)
