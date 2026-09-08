// ==============================================================================
// GESTIÓN DEL PANEL DE ADMINISTRACIÓN (USUARIOS, MODALES, DROPDOWNS Y CHECKBOXES)
// ==============================================================================

// 1. Selección múltiple de checkboxes en la tabla
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

// 3. Inicialización y Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // --- Listener por ID para abrir temporadas ---
    const btnAbrir = document.getElementById('btnAbrirTemporadas') || document.getElementById('btnModalTemporadas');
    const modal = document.getElementById('modalTemporadas');

    if (btnAbrir && modal) {
        btnAbrir.addEventListener('click', (e) => {
            e.preventDefault();
            window.abrirModalTemporadas();
        });
    }

    // --- Cierre del Modal con fondo o tecla Escape ---
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                window.cerrarModalTemporadas();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.style.display === 'flex') {
                window.cerrarModalTemporadas();
            }
        });
    }

    // --- Dropdown del Perfil de Usuario (Navbar) ---
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