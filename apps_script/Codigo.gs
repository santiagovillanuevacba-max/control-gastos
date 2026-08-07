/**
 * Control de Gastos · Santi — servidor web (Google Apps Script).
 *
 * Sirve la app `app/index.html` (la que genera el pipeline) leyéndola de tu
 * Google Drive. Ventaja: cuando actualizás los datos y se regenera index.html
 * en el Drive, la web se actualiza SOLA — no hace falta volver a publicar.
 *
 * Cómo usar: pegá abajo, entre las comillas, el ID del archivo app/index.html
 * en tu Drive (ver apps_script/README.md, paso 1). Después: Implementar → app web.
 */
const FILE_ID = 'PEGA_ACA_EL_ID_DEL_ARCHIVO';

function doGet() {
  const html = DriveApp.getFileById(FILE_ID).getBlob().getDataAsString('UTF-8');
  return HtmlService.createHtmlOutput(html)
    .setTitle('Control de Gastos · Santi')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover');
}
