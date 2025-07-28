// static/js/global-loader.js

document.addEventListener('DOMContentLoaded', function () {
    const loader = document.getElementById('global-loader');

    // Mostrar loader al enviar formularios POST (excepto los que tienen manejo especial)
    document.addEventListener('submit', function (e) {
        const form = e.target;

        if (form.id === 'ventaForm') return;

        if (form.method.toLowerCase() === 'post') {
            showLoader();
        }
    });

    // Interceptar todas las peticiones fetch
    const originalFetch = window.fetch;
    window.fetch = function (...args) {
        showLoader();

        return originalFetch.apply(this, args)
            .then(response => {
                // Esperar a que la respuesta esté lista
                if (response.ok) {
                    return response.clone().text().then(() => {
                        hideLoader();
                        return response;
                    });
                } else {
                    hideLoader();
                    return response;
                }
            })
            .catch(error => {
                hideLoader();
                throw error;
            });
    };

    // Mostrar loader al hacer clic en enlaces
    document.body.addEventListener('click', function (e) {
        const target = e.target.closest('a');

        if (target && target.tagName === 'A' && !target.hasAttribute('data-no-loader') && target.href && !target.href.startsWith('#')) {
            // Evita mostrarlo si es una ancla o no cambia de página
            showLoader();
        }
    });

    // Ocultar loader al finalizar completamente la carga de la página
    window.addEventListener('load', function () {
        hideLoader();
    });

    // Ocultar loader en navegación por historial (adelante/atrás)
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            hideLoader();
        }
    });

    function showLoader() {
        loader.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function hideLoader() {
        loader.style.display = 'none';
        document.body.style.overflow = '';
    }
});
