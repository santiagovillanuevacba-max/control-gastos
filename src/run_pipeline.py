#!/usr/bin/env python3
"""
run_pipeline.py — Orquestador del pipeline completo.

    python src/run_pipeline.py            # corre sobre datos de ejemplo (data/sample)
    python src/run_pipeline.py --real     # corre sobre resúmenes reales en data/raw

Etapas: parse (ingesta) -> transform (limpieza + categorización) -> build_app (front-end).
"""
import sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REAL = "--real" in sys.argv

def step(name, args):
    print(f"\n=== {name} ===")
    subprocess.run([sys.executable, str(ROOT / name), *args], check=True)

if REAL:
    step("parse_statements.py", [])                     # data/raw -> data/interim/all_tx.csv
    step("transform.py", [str(ROOT.parent / "data" / "interim" / "all_tx.csv")])
else:
    step("transform.py", [str(ROOT.parent / "data" / "sample" / "all_tx.csv")])
step("build_app.py", [])
print("\n[OK] Pipeline completo. Abri app/index.html")
