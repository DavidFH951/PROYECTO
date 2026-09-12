// ==============================================================================
// INTRANET - CONTROL DE MENÚ DRAWER MÓVIL Y DESPLEGABLE DE USUARIO (ACADEMIA GALENO)
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {

    // --------------------------------------------------------------------------
    // FUNCIONES BASE DE CONTROL DE SIDEBAR
    // --------------------------------------------------------------------------
    function toggleSidebarGeneral(open) {
        const sidebar = document.getElementById('sidebarGaleno') || 
                        document.getElementById('sidebar') ||
                        document.querySelector('.sidebar-galeno') ||
                        document.querySelector('.intranet-sidebar') ||
                        document.querySelector('aside');

        const backdrop = document.getElementById('sidebarBackdrop') || 
                         document.querySelector('.sidebar-backdrop');

        if (!sidebar) return;

        if (open) {
            sidebar.classList.add('drawer-open', 'active');
            if (backdrop) {
                backdrop.classList.add('active');
                backdrop.style.display = 'block';
            }
            document.body.style.overflow = 'hidden';
        } else {
            sidebar.classList.remove('drawer-open', 'active');
            if (backdrop) {
                backdrop.classList.remove('active');
                backdrop.style.display = '';
            }
            document.body.style.overflow = '';
        }
    }

    function toggleSidebarCurso(open) {
        const sidebarCurso = document.getElementById('sidebarCurso') || 
                             document.querySelector('.sidebar-curso-panel');
        const backdropCurso = document.getElementById('sidebarCursoBackdrop') || 
                              document.querySelector('.sidebar-curso-backdrop');

        if (!sidebarCurso) return;

        if (open) {
            sidebarCurso.classList.add('drawer-open', 'active');
            if (backdropCurso) {
                backdropCurso.classList.add('active');
                backdropCurso.style.display = 'block';
            }
            document.body.style.overflow = 'hidden';
        } else {
            sidebarCurso.classList.remove('drawer-open', 'active');
            if (backdropCurso) {
                backdropCurso.classList.remove('active');
                backdropCurso.style.display = '';
            }
            document.body.style.overflow = '';
        }
    }

    // --------------------------------------------------------------------------
    // 1. DISPARADOR GLOBAL UNIVERSAL (SOPORTE CLICK Y TOUCH EN MÓVILES)
    // --------------------------------------------------------------------------
    function manejarInteraccionMenu(e) {
        // A. Botón Hamburguesa de Aula Virtual (Semanas del curso)
        const btnCurso = e.target.closest('#btnHamburgerCurso, .btn-hamburger-curso');
        if (btnCurso) {
            e.preventDefault();
            e.stopPropagation();
            toggleSidebarCurso(true);
            return;
        }

        // B. Botón Hamburguesa Institucional (Topbar General y Docente)
        // Detecta el ID exacto, la clase btn-hamburger-intranet, atributos data o cualquier botón dentro del header
        const btnGeneral = e.target.closest(
            '#btnHamburgerSidebar, .btn-hamburger-intranet, #btnSidebarToggle, .btn-hamburger-topbar, .btn-hamburger, header .top-navbar button, button[data-sidebar-toggle="true"]'
        );
        const esTextoHamburguesa = e.target.textContent && e.target.textContent.trim() === '☰';

        if (btnGeneral || esTextoHamburguesa) {
            e.preventDefault();
            e.stopPropagation();
            toggleSidebarGeneral(true);
            return;
        }

        // C. Botón Cerrar (✕) o Clic en Fondo Oscuro (Backdrop)
        const btnCerrarGeneral = e.target.closest('#btnSidebarClose, .sidebar-close-btn, .btn-close-sidebar');
        const clickFondoGeneral = e.target.id === 'sidebarBackdrop' || (e.target.classList && e.target.classList.contains('sidebar-backdrop'));

        if (btnCerrarGeneral || clickFondoGeneral) {
            e.preventDefault();
            toggleSidebarGeneral(false);
            return;
        }

        const btnCerrarCurso = e.target.closest('#btnSidebarCursoClose, .btn-close-curso-sidebar');
        const clickFondoCurso = e.target.id === 'sidebarCursoBackdrop' || (e.target.classList && e.target.classList.contains('sidebar-curso-backdrop'));

        if (btnCerrarCurso || clickFondoCurso) {
            e.preventDefault();
            toggleSidebarCurso(false);
            return;
        }

        // D. Cerrar automáticamente al navegar en un link del menú
        if (e.target.closest('.sidebar-galeno a, .sidebar-curso-panel a')) {
            toggleSidebarGeneral(false);
            toggleSidebarCurso(false);
        }
    }

    document.addEventListener('click', manejarInteraccionMenu);

    // --------------------------------------------------------------------------
    // 2. DESPLEGABLE DE PERFIL DE USUARIO
    // --------------------------------------------------------------------------
    const trigger = document.getElementById('userProfileTrigger') || 
                    document.querySelector('.user-profile-trigger');
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

    // --------------------------------------------------------------------------
    // 3. MODAL DE HORARIOS
    // --------------------------------------------------------------------------
    const modalOverlay = document.getElementById('modalHorarioOverlay');
    const btnCerrarModal = document.getElementById('btnCerrarModalHorario');
    const txtTitulo = document.getElementById('modalCursoTitulo');
    const txtHora = document.getElementById('modalCursoHora');
    const txtAula = document.getElementById('modalCursoAula');
    const txtDocente = document.getElementById('modalCursoDocente');

    document.querySelectorAll('.js-event-clickable').forEach(tarjeta => {
        tarjeta.addEventListener('click', function () {
            const curso = this.getAttribute('data-curso') || 'Curso';
            const hora = this.getAttribute('data-hora') || '--:--';
            const aula = this.getAttribute('data-aula') || 'Virtual';
            const docente = this.getAttribute('data-docente') || 'Plana Médica Galeno';

            if (txtTitulo) txtTitulo.textContent = curso;
            if (txtHora) txtHora.textContent = hora;
            if (txtAula) txtAula.textContent = aula;
            if (txtDocente) txtDocente.textContent = docente;

            if (modalOverlay) modalOverlay.classList.add('active');
        });
    });

    if (btnCerrarModal && modalOverlay) {
        btnCerrarModal.addEventListener('click', () => {
            modalOverlay.classList.remove('active');
        });
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove('active');
            }
        });
    }
});

// Soporte retrocompatible para llamadas directas onclick
function toggleUserMenu(event) {
    if (event) event.stopPropagation();
    const container = document.querySelector('.user-dropdown-container');
    if (container) {
        container.classList.toggle('active');
    }
}