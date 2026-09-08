// ==============================================================================
// CONTROL DE TIEMPO, AUTOENVÍO Y MONITOREO DOCENTE (RENDIR EVALUACIÓN)
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {
    const reloj = document.getElementById('reloj-timer');
    const formulario = document.getElementById('form-examen');
    const btnEnviar = document.getElementById('btn-enviar-examen');

    if (!reloj || !formulario) return;

    // Obtener parámetros dinámicos desde atributos data-*
    const tiempoInicial = parseInt(reloj.getAttribute('data-tiempo') || '3600', 10);
    const urlVerificar = reloj.getAttribute('data-url-verificar') || '';

    let tiempoRestante = tiempoInicial;

    function actualizarReloj() {
        const minutos = Math.floor(tiempoRestante / 60);
        const segundos = tiempoRestante % 60;

        reloj.textContent =
            (minutos < 10 ? '0' : '') + minutos + ':' +
            (segundos < 10 ? '0' : '') + segundos;

        // Alerta visual al restar 5 minutos o menos
        if (tiempoRestante <= 300) {
            reloj.style.borderColor = '#ef4444';
            reloj.style.color = '#f87171';
            reloj.style.backgroundColor = '#450a0a';
        }

        // Agotamiento del tiempo
        if (tiempoRestante <= 0) {
            clearInterval(intervalo);
            if (monitorDocente) clearInterval(monitorDocente);

            reloj.textContent = "00:00";
            if (btnEnviar) {
                btnEnviar.disabled = true;
                btnEnviar.textContent = "Tiempo agotado. Guardando evaluación...";
            }
            alert("¡El tiempo límite ha concluido! Tus respuestas se enviarán automáticamente.");
            formulario.submit();
        } else {
            tiempoRestante--;
        }
    }

    actualizarReloj();
    const intervalo = setInterval(actualizarReloj, 1000);

    // Monitoreo remoto: consultar cada 5 segundos si el docente cerró la prueba
    let monitorDocente = null;
    if (urlVerificar) {
        monitorDocente = setInterval(function () {
            fetch(urlVerificar)
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    if (data && data.cerrado) {
                        clearInterval(monitorDocente);
                        clearInterval(intervalo);
                        alert("El docente ha finalizado la evaluación. Tus respuestas se enviarán automáticamente en este momento.");
                        formulario.submit();
                    }
                })
                .catch(function (err) {
                    console.error("Error comprobando estado:", err);
                });
        }, 5000);
    }
});