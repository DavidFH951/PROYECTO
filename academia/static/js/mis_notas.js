/* ==============================================================================
   LÓGICA DEL MODAL DE CALIFICACIONES (ALUMNO) - ACADEMIA GALENO
   ============================================================================== */

function abrirModalNotas(btn) {
    const titulo = btn.getAttribute('data-curso');
    const formula = btn.getAttribute('data-formula');
    const evalsRaw = btn.getAttribute('data-evals');
    
    const tituloElem = document.getElementById('modalCursoTitulo');
    const formulaElem = document.getElementById('modalFormulaTexto');
    const modalElem = document.getElementById('modalNotas');
    const tbody = document.getElementById('modalEvalBody');

    if (tituloElem) tituloElem.textContent = titulo;
    if (formulaElem) formulaElem.textContent = formula;
    if (!tbody || !modalElem) return;

    tbody.innerHTML = '';
    
    let evals = [];
    try {
        evals = JSON.parse(evalsRaw);
    } catch (e) {
        evals = [];
    }
    
    if (evals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 24px; color: #94a3b8;">No se han configurado evaluaciones para esta materia.</td></tr>';
    } else {
        evals.forEach(function(ev) {
            let scoreHtml = '';
            if (ev.nota !== null && ev.nota !== undefined && ev.nota !== '') {
                const numNota = parseFloat(ev.nota);
                const cls = numNota >= 10.5 ? 'score-pass' : 'score-fail';
                scoreHtml = `<span class="score-badge ${cls}">${numNota.toFixed(2)}</span>`;
            } else {
                scoreHtml = '<span class="score-badge score-pending">—</span>';
            }
            
            const row = `
                <tr>
                    <td><strong>${ev.nombre || ev.codigo}</strong></td>
                    <td style="text-align: center;"><span class="badge-code">${ev.codigo}</span></td>
                    <td style="text-align: center;">${scoreHtml}</td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', row);
        });
    }
    
    modalElem.style.display = 'flex';
}

function cerrarModalNotas() {
    const modalElem = document.getElementById('modalNotas');
    if (modalElem) {
        modalElem.style.display = 'none';
    }
}

function cerrarModalFondo(event) {
    if (event.target.id === 'modalNotas') {
        cerrarModalNotas();
    }
}

// Soporte para tecla Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        cerrarModalNotas();
    }
});