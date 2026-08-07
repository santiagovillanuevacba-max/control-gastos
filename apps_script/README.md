# Publicar la app en tu celu (Google Apps Script)

Objetivo: tener la app privada, con su propia URL, y un ícono en la pantalla del
celu — sin pasar por Claude. Los datos siguen siendo privados (solo tu cuenta).

La app web **lee `data/processed/app.html` de tu Google Drive** (esa es la app
con tus datos REALES; `app/index.html` es solo la demo pública). Cuando
actualizás los datos (`python src/run_pipeline.py --real`) la web se actualiza
sola, sin volver a publicar.

## Paso 1 — Conseguir el ID del archivo en Drive
1. Entrá a [drive.google.com](https://drive.google.com) y buscá el archivo
   `app.html` (está en `Control Gastos Santi/.../control-gastos/data/processed/`).
2. Click derecho → **Compartir** → **Copiar vínculo**.
3. El link es así: `https://drive.google.com/file/d/`**`ESTO_ES_EL_ID`**`/view`.
   Copiá el pedazo del medio (el ID).

## Paso 2 — Crear el proyecto Apps Script
1. Andá a [script.google.com](https://script.google.com) → **Proyecto nuevo**.
2. Borrá todo el código que aparece y pegá el contenido de `Codigo.gs`.
3. En la línea `const FILE_ID = '...'`, pegá el ID del Paso 1 entre las comillas.
4. Guardá (ícono 💾).

## Paso 3 — Publicar como app web
1. Arriba a la derecha: **Implementar** → **Nueva implementación**.
2. Engranaje ⚙️ → tipo **Aplicación web**.
3. Configurá:
   - **Ejecutar como:** Yo (tu cuenta).
   - **Quién tiene acceso:** **Solo yo** (privado).
4. **Implementar** → te pide **autorizar** (dale permiso para leer tu Drive).
5. Copiá la **URL de la aplicación web** (termina en `/exec`).

## Paso 4 — El ícono en el celu
1. Abrí esa URL en el navegador del celu (con tu cuenta de Google logueada).
2. Menú del navegador → **Agregar a pantalla de inicio**.
3. Listo: queda como una app, a pantalla completa. 📱

## Actualizar los datos más adelante
Solo corré `python src/run_pipeline.py --real` en la compu. Se regenera
`data/processed/app.html` en el Drive y la web toma la versión nueva sola. No
toques Apps Script de nuevo.
