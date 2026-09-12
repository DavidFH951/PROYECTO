// ==============================================================================
// INTRANET - CONTROL DE MENÚ DRAWER MÓVIL Y DESPLEGABLE DE USUARIO
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {
    // --- 1. MENÚ DRAWER LATERAL (MÓVIL) ---
    const btnOpen = document.getElementById('btnHamburgerSidebar');
    const btnClose = document.getElementById('btnSidebarClose');
    const sidebar = document.getElementById('sidebarGaleno');
    const backdrop = document.getElementById('sidebarBackdrop');

    function toggleSidebar(open) {
        if (!sidebar || !backdrop) return;
        if (open) {
            sidebar.classList.add('drawer-open');
            backdrop.classList.add('active');
            document.body.style.overflow = 'hidden'; // Bloquea scroll detrás del menú
        } else {
            sidebar.classList.remove('drawer-open');
            backdrop.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    if (btnOpen) {
        btnOpen.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleSidebar(true);
        });
    }

    if (btnClose) {
        btnClose.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleSidebar(false);
        });
    }

    if (backdrop) {
        backdrop.addEventListener('click', function () {
            toggleSidebar(false);
        });
    }

    // Cerrar drawer automáticamente si tocan un enlace dentro del menú
    if (sidebar) {
        sidebar.querySelectorAll('.sidebar-link').forEach(link => {
            link.addEventListener('click', () => toggleSidebar(false));
        });
    }

    // --- 2. CONTROL DEL DESPLEGABLE DE USUARIO ---
    const trigger = document.getElementById('userProfileTrigger') || document.querySelector('.user-profile-trigger');
    const container = document.querySelector('.user-dropdown-container');

    if (trigger && container) {
        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            container.classList.toggle('active');
        });

        document.addEventListener('click', function (e) {
            if (!container.contains(e.target)) {
                container.classList.remove('active');
            }
        });
    }
});

// Soporte retrocompatible para llamadas onclick="toggleUserMenu(event)" directas
function toggleUserMenu(event) {
    if (event) event.stopPropagation();
    const container = document.querySelector('.user-dropdown-container');
    if (container) {
        container.classList.toggle('active');
    }
}