#!/usr/bin/env python3
"""
parse_statements.py — Etapa de ingesta y parseo.

Convierte los resúmenes de cuenta crudos (PDF del banco, CSV de Mercado Pago)
que estén en data/raw/ en una tabla única y normalizada: data/interim/all_tx.csv
con columnas: source, account, date, desc, amount_ars, amount_usd, cuota, kind.

Cada cuenta tiene su propio "lector" porque el layout de cada resumen es distinto.
Los PDF de texto se leen con `pdftotext -layout` (poppler-utils).

NOTA: data/raw/ está en .gitignore — los resúmenes reales NUNCA se suben al repo.
Para el demo público se usa data/sample/all_tx.csv (datos ficticios).
"""
import csv, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "interim" / "all_tx.csv"
MONTHS = {'Ene':1,'Feb':2,'Mar':3,'Abr':4,'May':5,'Jun':6,'Jul':7,'Ago':8,'Sep':9,'Oct':10,'Nov':11,'Dic':12}

def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          capture_output=True, text=True).stdout

def ar(s):  # 1.234.567,89 -> float
    try: return float(s.strip().replace('.', '').replace(',', '.'))
    except: return None

def parse_bbva_tarjeta(text, account):
    """Resumen de tarjeta BBVA: bloque entre 'Consumos' y 'TOTAL CONSUMOS'."""
    out, collecting = [], False
    for ln in text.split('\n'):
        if re.search(r'Consumos\s+\w', ln): collecting = True; continue
        if 'TOTAL CONSUMOS' in ln: collecting = False; continue
        if not collecting: continue
        m = re.match(r'\s*(\d{2})-(\w{3})-(\d{2})\s+(.+)', ln)
        if not m: continue
        dd, mon, yy, rest = m.groups()
        date = f"20{yy}-{MONTHS.get(mon,0):02d}-{int(dd):02d}"
        cuota = ''
        cm = re.search(r'C\.(\d{2})/(\d{2})', rest)
        if cm: cuota = f"{int(cm.group(1))}/{int(cm.group(2))}"
        nums = re.findall(r'-?\d{1,3}(?:\.\d{3})*,\d{2}', rest)
        usd = 'USD' in rest.upper()
        ars_v = usd_v = ''
        if nums:
            v = ar(nums[-1])
            if usd: usd_v = v
            else: ars_v = v
        desc = re.sub(r'C\.\d{2}/\d{2}|-?\d{1,3}(?:\.\d{3})*,\d{2}|\bUSD\b', '', rest)
        desc = re.sub(r'\s{2,}', ' ', desc).strip()
        out.append(dict(source=account, account=account, date=date, desc=desc,
                        amount_ars=ars_v, amount_usd=usd_v, cuota=cuota, kind='consumo'))
    return out

def parse_mercadopago(path):
    out = []
    for ln in open(path, encoding='utf-8', errors='replace'):
        p = ln.rstrip('\n').split(';')
        if len(p) < 5 or not re.match(r'\d{2}-\d{2}-\d{4}', p[0]): continue
        dd, mm, yyyy = p[0].split('-')
        v = ar(p[3])
        if v is None: continue
        out.append(dict(source='MP', account='Mercado Pago', date=f"{yyyy}-{mm}-{dd}",
                        desc=p[1].strip(), amount_ars=v, amount_usd='', cuota='', kind='mp'))
    return out

# parse_bbva_caja y parse_dolarapp: mismos principios (ver docs/architecture.md).

def main():
    rows = []
    if not RAW.exists():
        print(f"[parse] No hay data/raw/. Poné ahí los resúmenes reales. (El demo usa data/sample/)")
        return
    for f in sorted(RAW.glob("**/*")):
        low = f.name.lower()
        if low.endswith(".csv") and "mercado" in low:
            rows += parse_mercadopago(f)
        elif low.endswith(".pdf") and ("visa" in low or "master" in low):
            acc = "Visa Credito" if "visa" in low else "Master Credito"
            rows += parse_bbva_tarjeta(pdf_text(f), acc)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["source","account","date","desc","amount_ars","amount_usd","cuota","kind"])
        w.writeheader(); w.writerows(rows)
    print(f"[parse] {len(rows)} transacciones -> {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
