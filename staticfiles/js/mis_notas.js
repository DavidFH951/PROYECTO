// ==============================================================================
// GESTIÓN DEL MODAL DE EVALUACIONES Y CALIFICACIONES
// ==============================================================================

function abrirModalNotas(boton) {
    const cursoTitulo = boton.getAttribute('data-curso') || 'Asignatura';
    const formula = boton.getAttribute('data-formula') || 'No definida';
    const promedio = boton.getAttribute('data-promedio');
    const evaluaciones = JSON.parse(boton.getAttribute('data-evaluaciones') || '[]');

    document.getElementById('modalCursoTitulo').textContent = cursoTitulo;
    document.getElementById('modalFormulaTexto').textContent = formula;

    const tbody = document.getElementById('modalEvaluacionesBody');
    tbody.innerHTML = '';

    if (evaluaciones.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: #94a3b8; padding: 18px;">No hay criterios de evaluación configurados.</td></tr>`;
    } else {
        evaluaciones.forEach(ev => {
            const tr = document.createElement('tr');

            let notaBadge = `<span class="score-badge score-pending">—</span>`;
            if (ev.nota !== null && ev.nota !== undefined && ev.nota !== '') {
                const val = parseFloat(ev.nota);
                const passClass = val >= 10.5 ? 'score-pass' : 'score-fail';
                notaBadge = `<span class="score-badge ${passClass}">${val.toFixed(2)}</span>`;
            }

            tr.innerHTML = `
                <td><span class="badge-code">${ev.codigo}</span></td>
                <td><strong>${ev.nombre}</strong></td>
                <td style="text-align: right;">${notaBadge}</td>
            `;
            tbody.appendChild(tr);
        });

        if (promedio && promedio !== 'None') {
            const numProm = parseFloat(promedio);
            const passClass = numProm >= 10.5 ? 'score-pass' : 'score-fail';
            const trProm = document.createElement('tr');
            trProm.style.backgroundColor = '#f8fafc';
            trProm.innerHTML = `
                <td colspan="2" style="font-weight: 700; color: #0f172a;">PROMEDIO FINAL</td>
                <td style="text-align: right;"><span class="score-badge ${passClass}">${numProm.toFixed(2)}</span></td>
            `;
            tbody.appendChild(trProm);
        }
    }

    const modal = document.getElementById('modalNotas');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function cerrarModalNotas() {
    const modal = document.getElementById('modalNotas');
    if (modal) {
        modal.style.display = 'none';
    }
}

window.addEventListener('click', function (e) {
    const modal = document.getElementById('modalNotas');
    if (modal && e.target === modal) {
        modal.style.display = 'none';
    }
})
function togglePeriodMenu(e) {
    e.stopPropagation();
    const menu = document.getElementById('periodMenuList');
    if (menu) menu.classList.toggle('show');
}
document.addEventListener('click', function (e) {
    const dropdown = document.getElementById('periodDropdown');
    const menu = document.getElementById('periodMenuList');
    if (menu && dropdown && !dropdown.contains(e.target)) menu.classList.remove('show');
});
