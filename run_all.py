"""Run the full pipeline in order. Usage: python run_all.py [--from N]

N is a script number (e.g. --from 4 resumes at 04_analysis.py, --from 12 at 12_returns_panel.py), not a position:
step 12 (returns panel) runs right after step 02 because step 03 uses its output (v2, decision A4).
Works on Windows, macOS and Linux (no make needed).
"""
import subprocess, sys, time
from pathlib import Path

STEPS = ["01_extract_nic.py", "02_build_long.py", "12_returns_panel.py", "03_build_panel.py", "04_analysis.py",
         "05_figures.py", "06_facultative.py", "07_validate.py", "08_system_gmm.py",
         "09_total_assets.py", "10_leave_one_out.py", "11_cr_mismatch.py", "13_threshold.py"]
start = 0
if "--from" in sys.argv:
    n = int(sys.argv[sys.argv.index("--from") + 1])
    start = next((i for i, s in enumerate(STEPS) if int(s[:2]) == n), None)
    if start is None: sys.exit(f"No step numbered {n}. Steps: {', '.join(STEPS)}")

src = Path(__file__).parent / "src"
for i, step in enumerate(STEPS):
    if i < start:
        continue
    print(f"\n=== Step {step[:2]}: {step} ===", flush=True)
    t = time.time()
    r = subprocess.run([sys.executable, step], cwd=src)
    if r.returncode != 0:
        sys.exit(f"Step {step} failed. Fix it, then rerun with: python run_all.py --from {int(step[:2])}")
    print(f"--- done in {time.time() - t:.1f}s")
print("\nPipeline complete. Tables: outputs/tables  Figures: outputs/figures  Data: data/processed")
