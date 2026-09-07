// ==============================================================================
// LÓGICA DE PÁGINA PÚBLICA (CARRUSEL HERO Y LEAD WHATSAPP)
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. LÓGICA DEL CARRUSEL ---
    let slideIndex = 0;
    const slides = document.querySelectorAll('.hero-slide');
    const dots = document.querySelectorAll('.slider-dot');
    const sliderWrapper = document.querySelector('.hero-slider-wrapper');
    let intervalo = null;

    if (slides.length > 1) {
        function mostrarSlide(index) {
            slides.forEach(slide => slide.classList.remove('active'));
            dots.forEach(dot => dot.classList.remove('active'));

            slideIndex = (index + slides.length) % slides.length;
            slides[slideIndex].classList.add('active');

            if (dots[slideIndex]) {
                dots[slideIndex].classList.add('active');
            }
        }

        function siguienteSlide() {
            mostrarSlide(slideIndex + 1);
        }

        function iniciarIntervalo() {
            detenerIntervalo();
            intervalo = setInterval(siguienteSlide, 5000);
        }

        function detenerIntervalo() {
            if (intervalo) clearInterval(intervalo);
        }

        dots.forEach(dot => {
            dot.addEventListener('click', function () {
                const idx = parseInt(this.getAttribute('data-index'), 10);
                mostrarSlide(idx);
                iniciarIntervalo();
            });
        });

        if (sliderWrapper) {
            sliderWrapper.addEventListener('mouseenter', detenerIntervalo);
            sliderWrapper.addEventListener('mouseleave', iniciarIntervalo);
        }

        iniciarIntervalo();
    }

    // --- 2. ENVÍO A WHATSAPP (EN NUEVA PESTAÑA) ---
    const formLead = document.getElementById('form-whatsapp-lead');
    if (formLead) {
        formLead.addEventListener('submit', function (e) {
            e.preventDefault();

            // Obtenemos el número desde el atributo data-whatsapp o fallback
            const rawNumber = formLead.getAttribute('data-whatsapp') || '51926901555';
            const numeroAdmin = rawNumber.replace(/\D/g, '');

            const curso = document.getElementById('lead-curso')?.value || 'No especificado';
            const nombres = document.getElementById('lead-nombres')?.value.trim() || '';
            const apellidos = document.getElementById('lead-apellidos')?.value.trim() || '';
            const dni = document.getElementById('lead-dni')?.value.trim() || '';
            const telefono = document.getElementById('lead-telefono')?.value.trim() || '';
            const correo = document.getElementById('lead-correo')?.value.trim() || '';

            const mensaje = `¡Hola Academia Galeno! Deseo solicitar informes para inscribirme:\n\n` +
                            `📚 *Curso:* ${curso}\n` +
                            `👤 *Postulante:* ${nombres} ${apellidos}\n` +
                            `🪪 *DNI:* ${dni}\n` +
                            `📱 *WhatsApp:* ${telefono}\n` +
                            `✉️ *Correo:* ${correo}\n\n` +
                            `Quedo a la espera de la información de vacantes y matrícula.`;

            const urlWa = `https://wa.me/${numeroAdmin}?text=${encodeURIComponent(mensaje)}`;

            const link = document.createElement('a');
            link.href = urlWa;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
});