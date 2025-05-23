import sys
import importlib

required_packages = [
    'flask',
    'flask_cors',
    'endaq',
    'pandas',
    'matplotlib',
    'seaborn',
    'PIL',  # Pillow
    'numpy',
    'reportlab',
    'plotly',
    'kaleido',
    'dotenv'
]

print("Checking required packages...")
missing_packages = []

for package in required_packages:
    try:
        importlib.import_module(package)
        print(f"✓ {package} is installed")
    except ImportError as e:
        print(f"✗ {package} is NOT installed: {e}")
        missing_packages.append(package)

if missing_packages:
    print("\nMissing packages:")
    for package in missing_packages:
        print(f"- {package}")
    print("\nPlease install missing packages using:")
    print("pip install " + " ".join(missing_packages))
else:
    print("\nAll required packages are installed!") 