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

def pdf_text_raw(path):  # DolarApp: -raw alinea fecha+importe; -layout los desalinea
    return subprocess.run(["pdftotext", "-raw", str(path), "-"],
                          capture_output=True, text=True).stdout

def us(s):  # 1,234.56 -> float (formato US que usa DolarApp)
    try: return float(s.replace(',', ''))
    except: return None

MESES_EN = {'JAN':1,'FEB':2,'MAR':3,'APR':4,'MAY':5,'JUN':6,
            'JUL':7,'AUG':8,'SEP':9,'OCT':10,'NOV':11,'DEC':12}

_NUM = re.compile(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$')
_DATE = re.compile(r'^(\d{2})-([A-Za-z]{3})-(\d{2})$')

def _filas_pdf(page):
    """Agrupa las palabras de la página en filas por su coordenada Y (top≈misma fila)."""
    rows = {}
    for w in page.extract_words():
        rows.setdefault(round(w['top'] / 3), []).append((w['x0'], w['text']))
    for k in sorted(rows):
        yield sorted(rows[k])

def parse_bbva_tarjeta(path, account):
    """Consumos de una tarjeta BBVA (Visa/Master), leídos con pdfplumber.

    pdftotext no alcanza: las 5 columnas (fecha·desc·cupón·PESOS·DÓLARES) se
    desalinean y el importe queda pegado al consumo de al lado. pdfplumber lee
    por coordenadas: separa PESOS (x~460) de DÓLARES (x~555) sin ambigüedad.
    Sólo se toman los consumos (sección entre el encabezado "Consumos" y
    "TOTAL CONSUMOS"); saldo anterior, pagos e impuestos se ignoran acá.
    Validado: la suma de consumos cierra contra el resumen (Visa/Master, ene-jul).
    """
    import pdfplumber  # perezoso: el modo demo (data/sample) no lo necesita
    out, seccion, last = [], None, None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for parts in _filas_pdf(page):
                toks = [t for _, t in parts]
                if 'TOTAL CONSUMOS' in " ".join(toks).upper():
                    seccion = None; continue
                if toks[0] == 'Consumos' and len(toks) <= 8:   # encabezado de la sección
                    seccion = 'consumos'; last = None; continue
                if seccion != 'consumos':
                    continue
                m = _DATE.match(toks[0])
                if m:  # arrastrar la última fecha (BBVA no la repite en cada renglón)
                    last = f"20{m.group(3)}-{MONTHS.get(m.group(2), 0):02d}-{int(m.group(1)):02d}"
                pesos = [ar(t) for x, t in parts if 440 <= x < 520 and _NUM.match(t)]
                dolar = [ar(t) for x, t in parts if x >= 520 and _NUM.match(t)]
                if not (pesos or dolar) or not last:
                    continue
                desc = " ".join(t for x, t in parts if 90 < x < 395 and not _NUM.match(t) and not _DATE.match(t))
                cm = re.search(r'C\.(\d{2}/\d{2})', desc)
                out.append(dict(source=account, account=account, date=last, desc=desc.strip(),
                                amount_ars=pesos[0] if pesos else '', amount_usd=dolar[0] if dolar else '',
                                cuota=cm.group(1) if cm else '', kind='consumo'))
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

def parse_dolarapp(path):
    """Resumen ARS de DolarApp. Se lee con pdftotext -raw (que alinea fecha e
    importe; -layout los desalinea y quedan mal apareados).

    DolarApp emite 2 resúmenes por mes (ARS y USD). Los consumos se cuentan EN
    PESOS desde el resumen ARS (decisión de Santi). El resumen USD son sólo
    conversiones ARS<->USDc, así que se omite acá; esas líneas ("Enviado/Recibido
    a DolarApp Mexico", "Conversión") se clasifican como Movimiento vía rules.csv.
    """
    text = pdf_text_raw(path)
    if 'GARPA' not in text.upper():
        return []  # el ARS lo emite "GARPA"; el USD dice "Dólares digitales": se omite
    # El año sale del encabezado en modo -layout (ahí "Fecha de inicio" y el valor
    # van en la misma línea; en -raw quedan separados y el regex falla).
    ym = re.search(r'Fecha de inicio\s+\d{1,2}\s+[A-Za-z]+\s+(\d{4})', pdf_text(path))
    year = ym.group(1) if ym else '2026'
    rx = re.compile(r'^([A-Z][a-z]{2})\s+(\d{1,2})\s+.+?\s+([+-])\s+([\d,]+(?:\.\d+)?)\s+ARS\s+(.+)$')
    out = []
    for ln in text.split('\n'):
        m = rx.match(ln.strip())
        if not m:
            continue
        mon, dd, sign, amt, desc = m.groups()
        mm = MESES_EN.get(mon.upper())
        v = us(amt)
        if not mm or v is None:
            continue
        if sign == '-':
            v = -v
        out.append(dict(source='DolarApp', account='DolarApp',
                        date=f"{year}-{mm:02d}-{int(dd):02d}", desc=desc.strip(),
                        amount_ars=v, amount_usd='', cuota='', kind='dolarapp'))
    return out

def parse_bbva_caja(path):
    """Movimientos de la caja de ahorro BBVA, leídos con pdfplumber por coordenadas.

    Sección entre el encabezado (FECHA/CONCEPTO/…/CRÉDITO) y "TOTAL MOVIMIENTOS".
    DÉBITO (x~385) y CRÉDITO (x~460) se separan por posición; el SALDO (x>500)
    se ignora. Arrastra la última fecha para importes en renglones sin fecha.
    Validado contra "TOTAL MOVIMIENTOS" (débitos y créditos, ene-jul).
    """
    import pdfplumber
    out, year, seccion, last = [], '', False, None
    with pdfplumber.open(path) as pdf:
        full = "\n".join((p.extract_text() or '') for p in pdf.pages)  # el "al:" puede estar en cualquier página
        y = re.search(r'al:\s*\d{2}/\d{2}/(\d{4})', full) or re.search(r'\b\d{2}/\d{2}/(20\d{2})', full)
        year = y.group(1) if y else '2026'
        for page in pdf.pages:
            rows = {}
            for w in page.extract_words():
                rows.setdefault(round(w['top'] / 3), []).append((w['x0'], w['text']))
            for k in sorted(rows):
                parts = sorted(rows[k]); toks = [t for _, t in parts]; line = " ".join(toks)
                if 'CONCEPTO' in line and 'CR' in line.upper():
                    seccion = True; continue
                if 'TOTAL' in line and 'MOVIMIENTO' in line.upper():
                    seccion = False; continue
                if not seccion:
                    continue
                m = re.match(r'(\d{2})/(\d{2})$', toks[0])
                if m:
                    last = f"{year}-{m.group(2)}-{m.group(1)}"
                deb = [ar(t) for x, t in parts if 360 <= x < 420 and _NUM.match(t)]
                cre = [ar(t) for x, t in parts if 420 <= x < 500 and _NUM.match(t)]
                val = deb[0] if deb else (cre[0] if cre else None)
                if val is None or not last:
                    continue
                desc = " ".join(t for x, t in parts if 125 <= x < 360 and not _NUM.match(t))
                out.append(dict(source='Caja', account='Caja de Ahorro', date=last,
                                desc=desc.strip(), amount_ars=val, amount_usd='', cuota='', kind='caja'))
    return out

def parse_mercadopago_pdf(path):
    """Resumen de Mercado Pago en PDF (formato distinto del CSV), con pdfplumber.

    Sólo la sección de PESOS: arranca en la cabecera de la tabla (Fecha/Valor) y
    corta al llegar a la sección en US$ (MP mete pesos y dólares en un mismo PDF).
    La descripción se parte en varias líneas; se asigna cada palabra a la fecha
    más cercana en Y. Validado contra Entradas/Salidas declaradas (abr-jul).
    """
    import pdfplumber
    _isdate = lambda t: re.match(r'\d{2}-\d{2}-\d{4}$', t)
    fechas, descs, started, in_usd = [], [], False, False
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages):
            rows = {}
            for w in page.extract_words():
                yy = w['top'] + pi * 2000
                rows.setdefault(round(yy / 3), []).append((w['x0'], yy, w['text']))
            for k in sorted(rows):
                parts = sorted(rows[k]); toks = [t for _, _, t in parts]; text = " ".join(toks)
                if not started:
                    if 'Fecha' in toks and 'Valor' in toks:
                        started = True
                    continue
                if 'US$' in text or 'EN US' in text.upper():
                    in_usd = True
                if in_usd:
                    continue
                if _isdate(toks[0]):
                    val = [ar(t) for x, _, t in parts if 250 < x < 335 and _NUM.match(t)]
                    if val:
                        fechas.append([toks[0], parts[0][1], val[0], []])
                for x, yy, t in parts:
                    if 85 <= x < 196 and re.search(r'[A-Za-z]', t) and not _isdate(t):
                        descs.append((yy, x, t))
    for yy, x, t in descs:
        if not fechas:
            continue
        i = min(range(len(fechas)), key=lambda j: abs(fechas[j][1] - yy))
        fechas[i][3].append((yy, x, t))
    out = []
    for f, yy, val, dw in fechas:
        dd, mm, yr = f.split('-')
        desc = " ".join(t for _, _, t in sorted(dw)).strip()
        out.append(dict(source='MP', account='Mercado Pago', date=f"{yr}-{mm}-{dd}",
                        desc=desc, amount_ars=val, amount_usd='', cuota='', kind='mp'))
    return out

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
            n = parse_bbva_tarjeta(f, "Visa Credito"); rows += n
            print(f"[parse] OK  {f.name}: Visa ({len(n)} consumos)")
        elif fmt == "bbva_master":
            n = parse_bbva_tarjeta(f, "Master Credito"); rows += n
            print(f"[parse] OK  {f.name}: Master ({len(n)} consumos)")
        elif fmt == "dolarapp":
            n = parse_dolarapp(f); rows += n
            etiq = f"DolarApp ARS ({len(n)} mov.)" if n else "DolarApp USD (conversiones, se omite)"
            print(f"[parse] OK  {f.name}: {etiq}")
        elif fmt == "bbva_caja":
            n = parse_bbva_caja(f); rows += n
            print(f"[parse] OK  {f.name}: Caja de ahorro ({len(n)} mov.)")
        elif fmt == "mercadopago_pdf":
            n = parse_mercadopago_pdf(f); rows += n
            print(f"[parse] OK  {f.name}: Mercado Pago PDF ({len(n)} mov.)")
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
