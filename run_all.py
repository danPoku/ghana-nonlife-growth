"""Run the full pipeline in order. Usage: python run_all.py [--from N]

Works on Windows, macOS and Linux (no make needed).
"""
import subprocess, sys, time
from pathlib import Path

STEPS = ["01_extract_nic.py", "02_build_long.py", "03_build_panel.py", "04_analysis.py",
         "05_figures.py", "06_facultative.py", "07_validate.py", "08_system_gmm.py",
         "09_total_assets.py", "10_leave_one_out.py", "11_cr_mismatch.py"]
start = 1
if "--from" in sys.argv:
    start = int(sys.argv[sys.argv.index("--from") + 1])

src = Path(__file__).parent / "src"
for i, step in enumerate(STEPS, 1):
    if i < start:
        continue
    print(f"\n=== Step {i}: {step} ===", flush=True)
    t = time.time()
    r = subprocess.run([sys.executable, step], cwd=src)
    if r.returncode != 0:
        sys.exit(f"Step {i} ({step}) failed. Fix it, then rerun with: python run_all.py --from {i}")
    print(f"--- done in {time.time() - t:.1f}s")
print("\nPipeline complete. Tables: outputs/tables  Figures: outputs/figures  Data: data/processed")
