// ==============================================================================
// GESTIÓN DEL PANEL DE ADMINISTRACIÓN (MODAL TEMPORADAS, DROPDOWNS Y CHECKBOXES)
// ==============================================================================

// 1. Selección múltiple de checkboxes en tablas administrativas
window.toggleAll = function (source) {
    const checkboxes = document.querySelectorAll('.user-check');
    checkboxes.forEach(function (cb) {
        cb.checked = source.checked;
    });
};

// 2. Control Global del Modal de Temporadas / Ciclos
window.abrirModalTemporadas = function () {
    const modal = document.getElementById('modalTemporadas');
    if (modal) {
        modal.style.display = 'flex';
    }
};

window.cerrarModalTemporadas = function () {
    const modal = document.getElementById('modalTemporadas');
    if (modal) {
        modal.style.display = 'none';
    }
};

// 3. Inicialización y Event Listeners globales
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modalTemporadas');

    // Cierre al hacer clic fuera del recuadro blanco
    window.addEventListener('click', (e) => {
        if (modal && e.target === modal) {
            window.cerrarModalTemporadas();
        }
    });

    // Cierre con la tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
            window.cerrarModalTemporadas();
        }
    });

    // Dropdown del Perfil de Usuario (Topbar)
    const userTrigger = document.querySelector('.user-profile-trigger');
    const userDropdown = document.querySelector('.user-dropdown-container');

    if (userTrigger && userDropdown) {
        userTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }
});