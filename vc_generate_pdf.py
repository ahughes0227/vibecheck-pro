import argparse
import datetime
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import endaq.ide

# -----------------------------------------------------------------------------
# EBML schema runtime fix
# -----------------------------------------------------------------------------
"""Ensure EBML‑lite schemas (mide_ide.xml, mide_bin.xml) are found both
in a normal Python install **and** when the app is frozen with PyInstaller.
The search order:
1️⃣ User‑set   ‑ If the env‑var EBML_SCHEMA_PATH already exists, honour it.
2️⃣ Frozen exe ‑ Look next to the exe ( …/ebmlite/schemata ).
3️⃣ Source env ‑ Look inside the installed ebmlite package.
The first directory that contains *mide_ide.xml* wins; it’s stored back
into EBML_SCHEMA_PATH so ebmlite.core finds it automatically.
"""
import os, sys, pathlib, importlib.util

def _ensure_schema_path():
    if os.getenv("EBML_SCHEMA_PATH"):
        return  # user or caller already set it

    candidate_dirs: list[pathlib.Path] = []

    # 1. If running frozen, schemas live beside the exe (copied by PyInstaller)
    if getattr(sys, "_MEIPASS", None):
        candidate_dirs.append(pathlib.Path(sys._MEIPASS) / "ebmlite" / "schemata")

    # 2. Normal site‑packages install
    spec = importlib.util.find_spec("ebmlite")
    if spec and spec.origin:
        candidate_dirs.append(pathlib.Path(spec.origin).parent / "schemata")

    for d in candidate_dirs:
        if (d / "mide_ide.xml").exists():
            os.environ["EBML_SCHEMA_PATH"] = str(d)
            break  # done

_ensure_schema_path()

# -----------------------------------------------------------------------------
# ReportLab imports
# -----------------------------------------------------------------------------
try:
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Image,
        Table,
        TableStyle,
        PageBreak,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter, landscape
except ImportError:
    print("Please install reportlab: pip install reportlab", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Project helpers
# -----------------------------------------------------------------------------
try:
    from vc_analyzer_endaq import analyze_endaq
    from vc_config import VC_THRESHOLDS
    from vc_plot_sensor_data import create_vc_plots_plotly, TEMP_PLOT_DIR_NAME
except ImportError as e:
    print(f"Missing project modules: {e}", file=sys.stderr)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def _lowest_vc_passed(values_mm_s: np.ndarray, vc_thresholds: dict[str, float]):
    """Return name of lowest VC level passed (or None)."""
    for name, thr in sorted(vc_thresholds.items(), key=lambda kv: kv[1]):
        if np.all(values_mm_s <= thr):
            return name
    return None


def _build_summary_table(sensor_data_list, vc_thresholds):
    header = ["Sensor", "Axis", "Lowest VC Passed"]
    rows: list[list[str]] = [header]

    if not sensor_data_list:
        rows.append(["No Sensor Data", "-", "-"])
    elif not vc_thresholds:
        rows.append(["-", "-", "VC thresholds missing"])
    else:
        for sensor in sensor_data_list:
            df = sensor["data"]
            for axis in ("X", "Y", "Z"):
                if df is None or df.empty or axis not in df.columns:
                    rows.append([sensor["name"], axis, "No data"])
                    continue
                freqs = pd.to_numeric(df.index, errors="coerce")
                band = df.loc[(freqs >= 1) & (freqs <= 100), axis].to_numpy() * 1000.0
                if band.size == 0:
                    rows.append([sensor["name"], axis, "No data"])
                    continue
                vc = _lowest_vc_passed(band, vc_thresholds)
                rows.append([sensor["name"], axis, vc if vc else "Fail"])

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, rl_colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ])
    for i, row in enumerate(rows[1:], 1):
        color = rl_colors.green if row[2] not in ("Fail", "No data") else rl_colors.red
        style.add("TEXTCOLOR", (2, i), (2, i), color)
    return rows, style


# -----------------------------------------------------------------------------
# PDF helpers
# -----------------------------------------------------------------------------

def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(doc.pagesize[0] - 0.5 * inch, 0.3 * inch, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


# -----------------------------------------------------------------------------
# Main PDF builder
# -----------------------------------------------------------------------------

def build_pdf_report(ide_path: str, pdf_path: str, location: str | None = None):
    print(f"[INFO] Building PDF → {pdf_path}")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    story: list = []

    # Header
    story.append(Paragraph("Vibration Analysis Report", ParagraphStyle("h1c", parent=styles["h1"], alignment=TA_CENTER)))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"Source File: {os.path.basename(ide_path)}", styles["Normal"]))
    loc_disp = "NA" if not location or location.strip().lower() in {"defaultlocation", "none", "-"} else location.strip()
    story.append(Paragraph(f"Location/Tool: {loc_disp}", styles["Normal"]))

    rec_date = "N/A"
    try:
        meta = endaq.ide.get_doc(ide_path)
        dt = getattr(getattr(meta, "summary", None), "start_time", None)
        if isinstance(dt, datetime.datetime):
            rec_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    if rec_date == "N/A":
        rec_date = datetime.datetime.fromtimestamp(os.path.getmtime(ide_path)).strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Recording Date: {rec_date}", styles["Normal"]))

    warn = ParagraphStyle("warn", parent=styles["Normal"], alignment=TA_CENTER, textColor=rl_colors.red)
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Warning: This report is auto-generated. Verify critical results.", warn))
    story.append(Spacer(1, 0.2 * inch))

    # Analyze IDE
    try:
        raw = analyze_endaq(ide_path)
    except Exception as e:
        story.append(Paragraph(f"<font color='red'>Error analyzing IDE: {e}</font>", styles["Normal"]))
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return

    sensors = []
    if isinstance(raw, tuple):
        if raw and raw[0] is not None and not raw[0].empty:
            sensors.append({"name": "25 g Sensor", "data": raw[0]})
        if len(raw) > 1 and raw[1] is not None and not raw[1].empty:
            sensors.append({"name": "40 g Sensor", "data": raw[1]})
    elif raw is not None and not raw.empty:
        sensors.append({"name": "25 g Sensor", "data": raw})

    story.append(Paragraph("Compliance Summary", styles["h2"]))
    tbl_data, tbl_style = _build_summary_table(sensors, VC_THRESHOLDS)
    tbl = Table(tbl_data, colWidths=[2.3 * inch, 0.7 * inch, 1.4 * inch])
    tbl.setStyle(tbl_style)
    story.append(tbl)

    # Plot section – always start on a new page so header stays with first image
    img_dir = os.path.join(tempfile.gettempdir(), TEMP_PLOT_DIR_NAME)
    tmp_html = os.path.join(img_dir, f"{os.path.splitext(os.path.basename(ide_path))[0]}_vc_plots.html")
    create_vc_plots_plotly(ide_path, tmp_html)

    pngs = [f for f in os.listdir(img_dir) if f.lower().endswith(".png") and os.path.splitext(os.path.basename(ide_path))[0] in f]
    pngs.sort()

    if pngs:
        story.append(PageBreak())
        story.append(Paragraph("Analysis Plots", styles["h2"]))
        story.append(Spacer(1, 0.1 * inch))

    for i, fn in enumerate(pngs):
        pth = os.path.join(img_dir, fn)
        img = Image(pth)
        # scale
        max_w, max_h = doc.width, doc.height - 1 * inch
        ratio = img.imageWidth / img.imageHeight
        w = min(max_w, img.imageWidth)
        h = w / ratio
        if h > max_h:
            h = max_h
            w = h * ratio
        img.drawWidth, img.drawHeight = w, h

        # border for visibility
        frame = Table([[img]], colWidths=[w], rowHeights=[h])
        frame.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.25, rl_colors.grey)]))
        story.append(frame)
        if i < len(pngs) - 1:
            story.append(PageBreak())

    # Build PDF
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print("[INFO] PDF build complete.")


# -----------------------------------------------------------------------------
# CLI wrapper
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate VibeCheck PDF report from .IDE file")
    parser.add_argument("ide_file", help="Path to .IDE file")
    parser.add_argument("-o", "--output", help="Output PDF path")
    parser.add_argument("-l", "--location", default="", help="Location/Tool name")
    args = parser.parse_args()

    if not os.path.isfile(args.ide_file):
        print("IDE file not found", file=sys.stderr)
        sys.exit(1)

    out_pdf = args.output or os.path.join(
        os.path.dirname(os.path.abspath(args.ide_file)),
        f"{os.path.splitext(os.path.basename(args.ide_file))[0]}_vc_report.pdf",
    )
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)

    build_pdf_report(args.ide_file, out_pdf, args.location)
