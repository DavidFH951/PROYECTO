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
// ==============================================================================
// 3. CONTROL DEL MODAL DE DETALLES DE HORARIO
// ==============================================================================
document.addEventListener('DOMContentLoaded', function () {
    const modalOverlay = document.getElementById('modalHorarioOverlay');
    const btnCerrarModal = document.getElementById('btnCerrarModalHorario');

    const txtTitulo = document.getElementById('modalCursoTitulo');
    const txtHora = document.getElementById('modalCursoHora');
    const txtAula = document.getElementById('modalCursoAula');
    const txtDocente = document.getElementById('modalCursoDocente');

    // Asignar clic a todas las tarjetas de clase
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
}

)
// --- CONTROL DE DRAWER PARA SIDEBAR DE CURSO ---
const btnOpenCurso = document.getElementById('btnHamburgerCurso');
const btnCloseCurso = document.getElementById('btnSidebarCursoClose');
const sidebarCurso = document.getElementById('sidebarCurso');
const backdropCurso = document.getElementById('sidebarCursoBackdrop');

function toggleSidebarCurso(open) {
    if (!sidebarCurso || !backdropCurso) return;
    if (open) {
        sidebarCurso.classList.add('drawer-open');
        backdropCurso.classList.add('active');
        document.body.style.overflow = 'hidden';
    } else {
        sidebarCurso.classList.remove('drawer-open');
        backdropCurso.classList.remove('active');
        document.body.style.overflow = '';
    }
}

if (btnOpenCurso) btnOpenCurso.addEventListener('click', () => toggleSidebarCurso(true));
if (btnCloseCurso) btnCloseCurso.addEventListener('click', () => toggleSidebarCurso(false));
if (backdropCurso) backdropCurso.addEventListener('click', () => toggleSidebarCurso(false));;