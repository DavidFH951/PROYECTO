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
});