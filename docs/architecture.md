# Arquitectura

## Flujo de datos

```
data/raw/*.pdf,*.csv
      │  parse_statements.py   (un "lector" por formato: BBVA tarjeta, BBVA caja, DolarApp, Mercado Pago)
      ▼
data/interim/all_tx.csv        (tabla normalizada: source, account, date, desc, amount_ars, amount_usd, cuota, kind)
      │  transform.py
      │    ├─ reglas de categorización  (config/rules.csv)
      │    ├─ transferencias internas   (etiquetas + pares mismo importe/fecha entre cuentas propias)
      │    ├─ compromisos futuros        (config/commitments.yaml)
      │    └─ taxonomía                  (config/categories.csv)
      ▼
data/processed/app_data.json
      │  build_app.py           (embebe el JSON en una app HTML de una sola página)
      ▼
app/index.html
```

## Decisiones de diseño

- **Config-driven**: nada de merchants ni categorías hardcodeados. Cambiar `config/` alcanza para
  ajustar el comportamiento o replicar el proyecto para otra persona.
- **App sin backend**: una sola página HTML que corre en el navegador; los datos se sincronizan
  con una Google Sheet (bridge Apps Script, en el roadmap). No depende de ningún servidor propio.
- **Validación contable**: cada resumen trae su total de control; el parseo se valida contra él.
- **Privacidad por diseño**: los datos reales viven fuera del repo (`.gitignore`).

## Parsers

Cada resumen tiene un layout distinto. Los PDF de texto se leen con `pdftotext -layout` y se
extraen las transacciones con expresiones regulares acotadas al bloque de consumos de cada
resumen, validando contra el total declarado. El CSV de Mercado Pago se parsea directo.
