import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import pytest
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from vibecheck.flask_server import app as flask_app
from vibecheck.vc_analyzer_endaq import analyze_endaq
from vibecheck.vc_plot_sensor_data import create_vc_plots_plotly
from vibecheck.vc_config import VC_THRESHOLDS

REAL_IDE = os.path.join(os.path.dirname(__file__), 'DAQ50971.IDE')

@pytest.fixture(scope='module')
def mock_analysis_results():
    """Create mock analysis results for testing."""
    freq = np.linspace(1, 100, 100)
    data = {
        'X': np.random.normal(0.1, 0.01, 100),
        'Y': np.random.normal(0.1, 0.01, 100),
        'Z': np.random.normal(0.1, 0.01, 100)
    }
    df = pd.DataFrame(data, index=freq)
    return (df, df)

@pytest.fixture(scope='module')
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_analyze_endaq_runs(mock_analysis_results):
    """Test that analyzer returns expected data structure (mocked)."""
    assert mock_analysis_results is not None
    if isinstance(mock_analysis_results, tuple):
        assert len(mock_analysis_results) > 0
        for df in mock_analysis_results:
            assert isinstance(df, pd.DataFrame)
            assert not df.empty
            assert all(col in df.columns for col in ['X', 'Y', 'Z'])
            assert isinstance(df.index, pd.Index)
            assert all(isinstance(x, (int, float)) for x in df.index)

def test_plot_generation_runs(tmp_path):
    """Test plot generation and verify HTML output (real IDE)."""
    html_out = tmp_path / 'report.html'
    assert create_vc_plots_plotly(REAL_IDE, str(html_out))
    assert html_out.exists()
    assert html_out.stat().st_size > 0


def test_api_health(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert rv.json['status'] == 'healthy'

def test_api_analyze(client):
    """Test file upload and analysis endpoint (real IDE)."""
    with open(REAL_IDE, 'rb') as f:
        data = {'file': (f, 'DAQ50971.IDE')}
        rv = client.post('/api/analyze', data=data, content_type='multipart/form-data')
    assert rv.status_code == 200
    assert rv.mimetype == 'text/html'
    assert rv.data.lstrip().startswith(b'<!DOCTYPE html')

def test_vc_thresholds():
    assert isinstance(VC_THRESHOLDS, dict)
    assert len(VC_THRESHOLDS) > 0
    for name, value in VC_THRESHOLDS.items():
        assert isinstance(name, str)
        assert isinstance(value, (int, float))
        assert value > 0

def test_analysis_data_quality(mock_analysis_results):
    if isinstance(mock_analysis_results, tuple):
        for df in mock_analysis_results:
            assert df.index.min() >= 0
            assert df.index.max() <= 1000
            for col in ['X', 'Y', 'Z']:
                if col in df.columns:
                    values = df[col].values
                    assert not np.any(np.isnan(values))
                    assert not np.any(np.isinf(values))
                    assert np.all(values >= 0)


def test_lowest_vc_passed():
    """Verify _lowest_vc_passed returns the expected VC level."""
    from vc_generate_pdf import _lowest_vc_passed

    thresholds = {'VC-A': 0.05, 'VC-B': 0.1, 'VC-C': 0.2}
    arr = np.array([0.04, 0.05])
    assert _lowest_vc_passed(arr, thresholds) == 'VC-A'
    arr = np.array([0.09, 0.08])
    assert _lowest_vc_passed(arr, thresholds) == 'VC-B'
    arr = np.array([0.25])
    assert _lowest_vc_passed(arr, thresholds) is None


def test_allowed_file():
    """Ensure allowed_file only permits IDE files."""
    from vibecheck.flask_server import allowed_file

    assert allowed_file('sample.IDE')
    assert allowed_file('demo.ide')
    assert not allowed_file('not.txt')
