// ==============================================================================
// INTRANET - CONTROL DEL DESPLEGABLE DE USUARIO (TÁCTIL Y DESKTOP)
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {
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

// Soporte por si tienes onclick="toggleUserMenu(event)" directo en el HTML:
function toggleUserMenu(event) {
    if (event) event.stopPropagation();
    const container = document.querySelector('.user-dropdown-container');
    if (container) {
        container.classList.toggle('active');
    }
}