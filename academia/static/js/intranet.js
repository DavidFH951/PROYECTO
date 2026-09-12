// ==============================================================================
// INTRANET - CONTROL DE MENÚ DRAWER MÓVIL Y DESPLEGABLE DE USUARIO (ACADEMIA GALENO)
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {

    // --------------------------------------------------------------------------
    // 1. CONTROL DE SIDEBAR GENERAL / PANEL DOCENTE / INTRANET
    // --------------------------------------------------------------------------
    // Busca por ID institucional o selectores alternativos comunes
    const btnOpen = document.getElementById('btnHamburgerSidebar') || 
                    document.getElementById('btnSidebarToggle') ||
                    document.querySelector('.top-navbar .btn-hamburger') ||
                    document.querySelector('.top-navbar button');

    const btnClose = document.getElementById('btnSidebarClose') || 
                     document.querySelector('.btn-close-sidebar');

    const sidebar = document.getElementById('sidebarGaleno') || 
                    document.getElementById('sidebar') ||
                    document.querySelector('.intranet-sidebar') ||
                    document.querySelector('.sidebar-galeno');

    const backdrop = document.getElementById('sidebarBackdrop') || 
                     document.querySelector('.sidebar-backdrop');

    function toggleSidebar(open) {
        if (!sidebar) return;
        if (open) {
            sidebar.classList.add('drawer-open');
            sidebar.classList.add('active');
            if (backdrop) backdrop.classList.add('active');
            document.body.style.overflow = 'hidden';
        } else {
            sidebar.classList.remove('drawer-open');
            sidebar.classList.remove('active');
            if (backdrop) backdrop.classList.remove('active');
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

    // Cerrar si tocan cualquier enlace del menú
    if (sidebar) {
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => toggleSidebar(false));
        });
    }

    // --------------------------------------------------------------------------
    // 2. CONTROL DEL SIDEBAR DE AULA VIRTUAL (CURSOS ESPECÍFICOS)
    // --------------------------------------------------------------------------
    const btnOpenCurso = document.getElementById('btnHamburgerCurso') || 
                         document.querySelector('.btn-hamburger-curso');

    const btnCloseCurso = document.getElementById('btnSidebarCursoClose') || 
                          document.querySelector('.btn-close-curso-sidebar');

    const sidebarCurso = document.getElementById('sidebarCurso') || 
                         document.querySelector('.sidebar-curso-panel');

    const backdropCurso = document.getElementById('sidebarCursoBackdrop') || 
                          document.querySelector('.sidebar-curso-backdrop');

    function toggleSidebarCurso(open) {
        if (!sidebarCurso) return;
        if (open) {
            sidebarCurso.classList.add('drawer-open');
            sidebarCurso.classList.add('active');
            if (backdropCurso) backdropCurso.classList.add('active');
            document.body.style.overflow = 'hidden';
        } else {
            sidebarCurso.classList.remove('drawer-open');
            sidebarCurso.classList.remove('active');
            if (backdropCurso) backdropCurso.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    if (btnOpenCurso) {
        btnOpenCurso.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleSidebarCurso(true);
        });
    }

    if (btnCloseCurso) {
        btnCloseCurso.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleSidebarCurso(false);
        });
    }

    if (backdropCurso) {
        backdropCurso.addEventListener('click', function () {
            toggleSidebarCurso(false);
        });
    }

    // --------------------------------------------------------------------------
    // 3. DESPLEGABLE DE PERFIL DE USUARIO
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
    // 4. MODAL DE HORARIOS
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

// Soporte retrocompatible para llamadas en línea onclick
function toggleUserMenu(event) {
    if (event) event.stopPropagation();
    const container = document.querySelector('.user-dropdown-container');
    if (container) {
        container.classList.toggle('active');
    }
}