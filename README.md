# 💸 Control de Gastos — pipeline de finanzas personales

Automatización end-to-end que lee los resúmenes de cinco cuentas (tarjetas de crédito BBVA,
caja de ahorro, DolarApp y Mercado Pago) en **seis formatos distintos** de PDF/CSV y los
convierte en una app web de control de gastos, sin carga manual. Detecta cada formato **por su
contenido** (no por el nombre del archivo), parsea, **valida al centavo** contra los totales del
resumen, categoriza y proyecta los compromisos futuros.

> Proyecto personal y a la vez pieza de portfolio de **ingeniería de datos + BI**.
> Los datos del demo son **ficticios**; los datos reales nunca se suben al repo.

![demo](docs/demo_resumen.png)

---

## El problema

Tenía gastos repartidos en cinco cuentas (dos tarjetas de crédito, débito, una billetera en
dólares y Mercado Pago) y ni idea de en qué se me iba la plata. Las planillas manuales que
intenté antes eran demasiado trabajo y las abandonaba. La solución tenía que ser **automática**
en lo repetitivo (resúmenes) y de **mínima fricción** en lo variable (Mercado Pago).

## Qué hace

- **Ingesta + parseo** de 6 formatos (BBVA tarjeta y caja, DolarApp, Mercado Pago CSV y PDF),
  detectados **por contenido**. Las tablas con columnas desalineadas se leen por **coordenadas**
  con `pdfplumber`; el resto con `pdftotext`.
- **Validación contable**: cada cuenta se cuadra **al centavo** contra el total de control del resumen.
- **Categorización automática (~80%)** con reglas configurables (un "machete" texto → categoría) +
  memoria de destinatarios y recategorización de cualquier movimiento desde la app.
- **Modelado de dominio**: transferencias internas, compensaciones con terceros, compra/venta de
  dólares y percepción sobre consumos en USD, todo tratado como corresponde (no infla el gasto).
- **App web** mobile-first (una sola página, sin backend), servible **privada desde el celu**
  vía Google Apps Script.

## Arquitectura

```
 Resúmenes            PYTHON PIPELINE                       CONSUMO
 (PDF / CSV)   ┌──────────────────────────────┐    ┌───────────────────────┐
   data/raw ──▶│ parse → transform → build_app│──▶ │ app web  +  Looker Studio│
               └──────────────────────────────┘    └───────────────────────┘
                 config-driven (config/*.csv,yaml)     Google Sheet (base)
```

1. **parse** (`src/parse_statements.py`) — PDF/CSV → tabla normalizada.
2. **transform** (`src/transform.py`) — limpieza, categorización, internas, futuros → `app_data.json`.
3. **build_app** (`src/build_app.py`) — genera la app web de una sola página.

Todo es **config-driven**: reglas, categorías y cuentas viven en `/config`, así el proyecto
se **replica** para otra persona sin tocar el código.

## Stack

`Python 3` (ETL, sin frameworks) · `pdfplumber` + `pdftotext` (lectura de PDF) · `PyYAML` (config) ·
`HTML/JS` vanilla (app) · `Google Apps Script` (deploy privado en el celu) · `Git` / `GitHub`.
*Roadmap:* `Google Sheets` + `Looker Studio` para la capa de análisis pesado.

## Correr el demo

```bash
pip install -r requirements.txt         # PyYAML + pdfplumber (además: pdftotext del sistema)
python src/run_pipeline.py              # usa data/sample (datos ficticios)
open app/index.html                     # abrir la app generada
```

Con datos reales: poné los resúmenes en `data/raw/` y corré `python src/run_pipeline.py --real`.

## Estructura

```
config/       reglas.csv · categories.csv · accounts.yaml · commitments.yaml
src/          parse_statements.py · transform.py · build_app.py · run_pipeline.py
data/         raw (gitignored) · interim · processed · sample (demo ficticio)
app/          index.html  (app generada)
.github/      workflows/pipeline.yml
```

## Privacidad

`data/raw/`, `interim/` y `processed/` están en `.gitignore`: **los números reales nunca salen
de la máquina**. El repo público muestra el *código y la arquitectura*, corriendo sobre datos
de ejemplo inventados.

## Roadmap

- [x] Pipeline: 6 lectores por contenido, **validados al centavo**
- [x] Categorización automática (~80%) + recategorización desde la app
- [x] App privada en el celu (Google Apps Script)
- [ ] Proyección de compromisos **calculada desde los datos reales** (hoy es config manual)
- [ ] Google Sheet + dashboards en Looker Studio
- [ ] Recordatorios automáticos (carga diaria y de resúmenes)

---

Hecho por Santiago Villanueva — Contador Público & Data/BI Analyst.
