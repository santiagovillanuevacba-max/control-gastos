# CLAUDE.md — contexto del proyecto para Claude Code

Este archivo le da a Claude Code el contexto completo del proyecto. Leelo antes de trabajar.

## Qué es

App de finanzas personales de Santiago Villanueva. Doble objetivo:
1. **Uso personal**: controlar gastos de 5 cuentas con la mínima fricción diaria.
2. **Portfolio**: pieza de ingeniería de datos + BI para mostrar en LinkedIn (repo público, datos reales privados).

Santi es Contador Público y analista de datos/BI (Power BI, Looker Studio, SQL; Python en progreso).
Al explicar o construir, priorizá claridad y que él pueda **entender y defender** el código, no soluciones "mágicas".

## Arquitectura

Pipeline en Python, config-driven, que termina en una app web:

```
data/raw/ (PDF, CSV)  →  parse_statements.py  →  data/interim/all_tx.csv
                         →  transform.py       →  data/processed/app_data.json
                         →  build_app.py       →  app/index.html
```

- **parse_statements.py**: un "lector" por formato (BBVA tarjeta, BBVA caja, DolarApp, Mercado Pago). PDFs con `pdftotext -layout`.
- **transform.py**: categorización, transferencias internas, compromisos futuros, taxonomía. Todo lee de `/config`.
- **build_app.py**: embebe el JSON en una app HTML de una sola página, mobile-first, sin backend.
- **run_pipeline.py**: orquesta todo. `--real` usa data/raw; sin flag usa data/sample (datos ficticios del demo).

### Config (nada hardcodeado — así se replica para otra persona)
- `config/rules.csv`: "machete" de categorización, `texto_contiene → tipo,subcategoria`. Prioridad máxima.
- `config/categories.csv`: taxonomía categoría → subcategoría.
- `config/accounts.yaml`: cuentas, titular, cuentas internas, dólar por defecto.
- `config/commitments.yaml`: cuotas de tarjeta, préstamo y recurrentes → vista "Futuro".

## Reglas de dominio (importantes, salieron de decisiones con Santi)

- **Transferencias internas**: mismo importe + misma fecha entre cuentas propias (MP/DolarApp/Visa débito), o etiquetas de pago de tarjeta, se compensan → NO son gasto ni ingreso (categoría "Movimiento").
- **Ingreso propio vs ayuda familiar**: separar la ayuda ("Transferencia Personal") del ingreso propio.
- **Ahorro**: reservas de "Vacaciones" y compra de dólares NO son gasto (son Ahorro / Movimiento).
- **USD**: expresar consumos en dólares a la cotización real de cada resumen.
- **Pendientes**: lo que no matchea ninguna regla (transferencias a personas) queda "sin categoría" para que Santi lo etiquete; hay memoria de destinatario (forward-only: aplica de ahí en adelante).
- **Deduplicación**: gastos que Santi carga a mano son provisorios; al importar el resumen se concilian por importe+fecha+cuenta para no duplicar.

## Estado y roadmap

- [x] Pipeline + app web (datos ene–mar 2026) — repo público en GitHub.
- [ ] **Backend en Google Apps Script + Google Sheet privada** → app con link privado y datos reales (EN CURSO). Sheet base ya creada en el Drive de Santi.
- [ ] Cargar meses recientes de todas las cuentas.
- [ ] Dashboards en Looker Studio sobre la Sheet.
- [ ] Cerrar la taxonomía (Santi la edita en config/categories.csv).

## Operación (vive en Cowork, no en Claude Code)

Los recordatorios son tareas programadas de Cowork/Claude app (no de este repo):
- Día 10 de cada mes: aviso por mail/push para subir los resúmenes.
- Chequeo diario de gastos en días hábiles (se activa con la app/Sheet).

## Privacidad

`data/raw/`, `interim/`, `processed/` están en `.gitignore`. Los números reales NUNCA se suben.
El repo público corre sobre `data/sample/` (ficticio). No pongas datos reales en commits.

## Convenciones

- Python estándar, sin frameworks pesados. Dependencias mínimas (ver requirements.txt).
- Mensajes y comentarios en español (es el idioma del proyecto).
- Antes de agregar una categoría o merchant, va en `/config`, no en el código.
