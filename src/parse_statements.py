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
# TODO: sus lectores todavía están pendientes; hoy se detectan pero no se parsean.

def detect_format(path):
    """Identifica el formato mirando el CONTENIDO del archivo, no su nombre.

    Así el archivo puede llamarse como sea (incluso con typos): lo que manda es
    lo que dice adentro. Devuelve (formato, texto) donde `texto` es el texto ya
    extraído del PDF (o None para CSV), para no volver a leerlo después.
    """
    suf = path.suffix.lower()
    if suf == ".csv":
        head = path.read_text(encoding="utf-8", errors="replace")[:2000].upper()
        if "RELEASE_DATE" in head and "TRANSACTION_NET_AMOUNT" in head:
            return "mercadopago", None
        return None, None
    if suf == ".pdf":
        text = pdf_text(path)
        up = text.upper()
        head = up[:2000]  # el encabezado alcanza para identificar la cuenta
        # Caja y DolarApp: huellas muy distintivas en el encabezado.
        if "CUENTAS Y PAQUETES" in head:
            return "bbva_caja", text
        if "ESTADO DE CUENTA" in head and ("GARPA" in up or "BALANCE DE INICIO" in up):
            return "dolarapp", text
        # Mercado Pago en PDF (distinto del CSV): título + CVU (billetera, no CBU).
        if "RESUMEN DE CUENTA" in head and "CVU" in up:
            return "mercadopago_pdf", text
        # Tarjetas BBVA: el código R.N.P.S.P. "731 V01"/"731 M01" es la huella
        # única de cada tarjeta. NO mirar todo el doc: un resumen Visa menciona
        # "Mastercard" en la letra chica de comisiones (y viceversa).
        if "731 M01" in head or ("MASTERCARD" in head and "VISA" not in head):
            return "bbva_master", text
        if "731 V01" in head or ("VISA" in head and "MASTERCARD" not in head):
            return "bbva_visa", text
    return None, None

def main():
    if not RAW.exists():
        print("[parse] No hay data/raw/. Poné ahí los resúmenes (con cualquier nombre).")
        return
    rows, pendientes, desconocidos = [], [], []
    for f in sorted(RAW.glob("**/*")):
        if not f.is_file():
            continue
        fmt, text = detect_format(f)
        if fmt == "mercadopago":
            n = parse_mercadopago(f); rows += n
            print(f"[parse] OK  {f.name}: Mercado Pago ({len(n)} mov.)")
        elif fmt == "bbva_visa":
            n = parse_bbva_tarjeta(text, "Visa Credito"); rows += n
            print(f"[parse] OK  {f.name}: Visa ({len(n)} mov.)")
        elif fmt == "bbva_master":
            n = parse_bbva_tarjeta(text, "Master Credito"); rows += n
            print(f"[parse] OK  {f.name}: Master ({len(n)} mov.)")
        elif fmt in ("bbva_caja", "dolarapp", "mercadopago_pdf"):
            pendientes.append((f.name, fmt))
            print(f"[parse] ..  {f.name}: {fmt} detectado (lector pendiente, se omite)")
        else:
            desconocidos.append(f.name)
            print(f"[parse] ??  {f.name}: formato no reconocido, se saltea")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["source","account","date","desc","amount_ars","amount_usd","cuota","kind"])
        w.writeheader(); w.writerows(rows)
    print(f"[parse] {len(rows)} transacciones -> {OUT.relative_to(ROOT)}")
    if pendientes:
        print(f"[parse] pendientes de lector: {', '.join(n for n, _ in pendientes)}")
    if desconocidos:
        print(f"[parse] no reconocidos: {', '.join(desconocidos)}")

if __name__ == "__main__":
    main()
