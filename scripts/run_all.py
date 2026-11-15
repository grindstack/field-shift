"""Run the whole pipeline: python scripts\\run_all.py"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["01_clean_data.py", "02_build_master.py", "03_quality_report_and_plots.py"]

for step in STEPS:
    print("\n" + "#" * 70 + f"\n# {step}\n" + "#" * 70)
    result = subprocess.run([sys.executable, str(HERE / step)], cwd=str(HERE.parent))
    if result.returncode != 0:
        print(f"\nStopped: {step} failed. Read the error above.")
        sys.exit(result.returncode)
print("\nALL DONE. Results: data/processed/ and reports/")
