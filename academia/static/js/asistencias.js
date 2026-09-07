// Control de acordeón para las materias en Asistencias
function toggleDetalle(id, btn) {
    const panel = document.getElementById(id);
    if (!panel) return;

    const flecha = btn.querySelector('.flecha-indicador');
    const estaAbierto = panel.style.display === 'block';

    if (estaAbierto) {
        panel.style.display = 'none';
        if (flecha) flecha.textContent = '▼';
        btn.classList.remove('activo');
    } else {
        panel.style.display = 'block';
        if (flecha) flecha.textContent = '▲';
        btn.classList.add('activo');
    }
}