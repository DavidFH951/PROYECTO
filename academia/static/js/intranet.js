// Control del menú desplegable de usuario en la Intranet
function toggleUserMenu(event) {
    if (event) {
        event.stopPropagation();
    }
    const menu = document.getElementById('userMenuDropdown');
    if (menu) {
        menu.classList.toggle('show');
    }
}

// Cerrar el dropdown al hacer clic fuera
document.addEventListener('click', function (e) {
    const menu = document.getElementById('userMenuDropdown');
    const container = document.querySelector('.user-dropdown-container');

    if (menu && menu.classList.contains('show')) {
        if (!container || !container.contains(e.target)) {
            menu.classList.remove('show');
        }
    }
})
document.addEventListener('DOMContentLoaded', function () {
    const trigger = document.getElementById('userProfileTrigger');
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