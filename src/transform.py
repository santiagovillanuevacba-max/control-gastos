#!/usr/bin/env python3
"""
transform.py — Etapa de transformación del pipeline.

Toma las transacciones crudas (data/interim/all_tx.csv o data/sample/all_tx.csv),
aplica las reglas de categorización (config/rules.csv), detecta transferencias
internas entre cuentas propias, arma los compromisos futuros y produce
data/processed/app_data.json, que consume la app web.

Todo es config-driven: las reglas, las categorías y las cuentas viven en /config,
así el proyecto se replica para otra persona sin tocar el código.
"""
import csv, json, re, sys, os, unicodedata
from pathlib import Path
from collections import defaultdict
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"

def noac(s):
    """minúsculas y sin acentos, para que las reglas matcheen 'dólares' == 'dolares'."""
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def load_rules():
    rows = list(csv.DictReader(open(CONFIG / "rules.csv", encoding="utf-8")))
    return [(noac(r["texto_contiene"]), r["tipo"], r["subcategoria"]) for r in rows]

def load_taxonomy():
    tax = defaultdict(list)
    for r in csv.DictReader(open(CONFIG / "categories.csv", encoding="utf-8")):
        tax[r["Categoría"]].append(r["Subcategoría"])
    return dict(tax)

def load_settings():
    return yaml.safe_load(open(CONFIG / "accounts.yaml", encoding="utf-8"))

def load_commitments():
    return yaml.safe_load(open(CONFIG / "commitments.yaml", encoding="utf-8"))

def ar_num(s):
    if s is None or s == "": return None
    try: return float(s)
    except: return None

def main(inp):
    rules = load_rules()
    tax = load_taxonomy()
    settings = load_settings()
    commit = load_commitments()
    subparent = {s: c for c, subs in tax.items() for s in subs}
    titular = (settings.get("titular") or "").lower().split()

    rows = list(csv.DictReader(open(inp, encoding="utf-8")))
    for r in rows:
        r["amount_ars"] = ar_num(r.get("amount_ars")) or 0.0
        r["amount_usd"] = ar_num(r.get("amount_usd")) or 0.0
        r["month"] = r["date"][:7]

    # --- transferencias internas: etiquetas explícitas + pares (mismo importe/fecha) ---
    EXPL = re.compile(r"pago de tarjeta|pago visa|pago mast|recibido de dolarapp|"
                      r"enviado a dolarapp|env[ií]o a dolarapp|env[ií]o ars", re.I)
    for r in rows:
        d = (r["desc"] or "").lower()
        r["internal"] = bool(EXPL.search(r["desc"] or ""))
        # transferencia a/desde uno mismo (nombre del titular) = interna, no ingreso ni gasto
        if titular and len(titular) >= 2 and all(w in d for w in titular):
            r["internal"] = True
    by_key = defaultdict(list)
    for i, r in enumerate(rows):
        if r["amount_ars"]:
            by_key[(r["date"], round(abs(r["amount_ars"])))].append(i)
    for _, idxs in by_key.items():
        outs = [i for i in idxs if rows[i]["amount_ars"] < 0]
        ins = [i for i in idxs if rows[i]["amount_ars"] > 0]
        for o in outs:
            for n in ins:
                if rows[o]["account"] != rows[n]["account"] and not rows[o]["internal"] and not rows[n]["internal"]:
                    rows[o]["internal"] = rows[n]["internal"] = True
                    break

    # --- categorización ---
    def classify(t):
        dl = noac(t["desc"])
        for txt, tipo, sub in rules:
            if txt and txt in dl:
                if tipo == "Movimiento": return ("Movimiento", sub or "TRF Entre Cuentas", "mov")
                if tipo == "Ahorro": return ("Ahorro & Inversiones", sub, "ahorro")
                if tipo == "Ingreso": return ("Ingresos", sub, "ingreso")
                return (subparent.get(sub, "Otros/Imprevistos"), sub, "gasto")
        # ingreso: cualquier crédito recibido y positivo (transferencias, depósitos).
        # Las transferencias a uno mismo ya se marcaron internas antes, así que acá
        # sólo caen las que vienen de terceros.
        if t["amount_ars"] > 0 and re.search(r"recibida|transferencia|deposito|dnet credito", dl):
            return ("Ingresos", "Otros ingresos", "ingreso")
        return ("", "", "pend")

    for r in rows:
        c, s, k = classify(r)
        # una transferencia interna (a uno mismo / pago de tarjeta / conversión) SIEMPRE
        # es Movimiento, aunque parezca ingreso: es plata propia moviéndose de cuenta.
        if k == "mov" or r["internal"]:
            r["cat"], r["subcat"], r["flow"] = "Movimiento", "TRF Entre Cuentas", "mov"
            r["internal"] = True
        else:
            r["cat"], r["subcat"], r["flow"] = c, s, k

    # --- compromisos futuros ---
    rec = commit.get("recurrente_mensual", {})
    rec_total = sum(rec.values())
    months_fut = sorted(set(list(commit.get("cuotas_tarjeta", {})) + list(commit.get("prestamo", {}))))
    future = []
    for m in months_fut:
        cu = commit.get("cuotas_tarjeta", {}).get(m, 0)
        pr = commit.get("prestamo", {}).get(m, 0)
        future.append({"month": m, "cuotas": cu, "prestamo": pr,
                       "recurrente": rec_total, "total": cu + pr + rec_total})

    # --- export ---
    def keep(r):
        d = (r["desc"] or "").lower()
        if "dinero retirado" in d: return False
        return r["amount_ars"] or r["amount_usd"]
    months = sorted({r["month"] for r in rows})
    tx = []
    for i, r in enumerate(rows):
        if not keep(r): continue
        tx.append({"id": f"{r['date']}|{i}", "date": r["date"], "account": r["account"],
                   "desc": r["desc"], "ars": round(r["amount_ars"], 2), "usd": round(r["amount_usd"], 2),
                   "cuota": r.get("cuota") or "", "kind": r.get("kind", ""), "month": r["month"],
                   "internal": r["internal"], "cat": r["cat"], "subcat": r["subcat"],
                   "flow": r["flow"], "isIncome": r["flow"] == "ingreso"})
    tx.sort(key=lambda x: x["date"])
    bundle = {"generated": "sample", "usd_rate": settings.get("usd_ars_default", 1450),
              "months": months, "taxonomy": tax, "future": future, "recurring": rec, "tx": tx}
    out = ROOT / "data" / "processed" / "app_data.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(bundle, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    pend = sum(1 for t in tx if t["flow"] == "pend")
    print(f"[transform] {len(tx)} transacciones · {pend} pendientes · {len(months)} meses -> {out.relative_to(ROOT)}")

if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data" / "sample" / "all_tx.csv")
    main(inp)
