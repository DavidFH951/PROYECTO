/* ==============================================================================
   INTERACTIVIDAD DASHBOARD DOCENTE - ACADEMIA GALENO
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const userBtn = document.querySelector('.user-profile-badge-btn');
    const userMenu = document.getElementById('userDropdownDocente');

    if (userBtn && userMenu) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('show');
        });

        window.addEventListener('click', (e) => {
            if (!userMenu.contains(e.target) && userMenu.classList.contains('show')) {
                userMenu.classList.remove('show');
            }
        });
    }
});