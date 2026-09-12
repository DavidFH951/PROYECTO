/* ==========================================================================
   CARGA MASIVA DE USUARIOS - ACADEMIA GALENO
   ========================================================================== */

/**
 * Genera y descarga una plantilla CSV con compatibilidad directa para Excel en español:
 * Incluye cabecera 'sep=;' y prefijo BOM UTF-8 (\uFEFF) para abrir celdas A-F separadas.
 */
function descargarPlantillaCSV() {
    const lineas = [
        "sep=;",
        "username;first_name;last_name;email;password;rol",
        "jperez;Juan;Perez Garcia;jperez@galeno.pe;Temporal123*;Alumnos",
        "mrodriguez;Maria;Rodriguez Soto;mrodriguez@galeno.pe;Temporal123*;Docentes"
    ];
    const contenido = lineas.join("\r\n");

    const blob = new Blob(["\uFEFF" + contenido], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "plantilla_usuarios_galeno.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Muestra visualmente el nombre del archivo seleccionado en el dropzone.
 */
function mostrarNombreArchivo(input) {
    const display = document.getElementById('fileSelectedName');
    if (input.files && input.files[0]) {
        display.innerText = 'Archivo cargado: ' + input.files[0].name;
        display.style.display = 'block';
    } else {
        display.style.display = 'none';
    }
}