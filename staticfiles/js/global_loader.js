document.addEventListener('DOMContentLoaded', function () {
    const loader = document.getElementById('global-loader');
    let loaderTimeout;
    const LOADER_DELAY = 300; // ms para otras operaciones (no aplica a clics en enlaces)
    let isLinkClick = false; // Bandera para identificar clics en enlaces

    // Mostrar loader con comportamiento diferenciado
    function showLoader() {
        clearTimeout(loaderTimeout);
        
        if (isLinkClick) {
            // Mostrar inmediatamente para clics en enlaces
            loader.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            document.documentElement.style.cursor = 'wait';
            isLinkClick = false; // Resetear bandera
        } else {
            // Para otras operaciones, mantener el retardo
            loaderTimeout = setTimeout(() => {
                loader.style.display = 'flex';
                document.body.style.overflow = 'hidden';
                document.documentElement.style.cursor = 'wait';
            }, LOADER_DELAY);
        }
    }

    function hideLoader() {
        clearTimeout(loaderTimeout);
        loader.style.display = 'none';
        document.body.style.overflow = '';
        document.documentElement.style.cursor = '';
    }

    // 1. Manejo de navegación (links) - Aquí activamos la bandera
    document.body.addEventListener('click', function (e) {
        const target = e.target.closest('a');
        if (target && target.tagName === 'A' && 
            !target.hasAttribute('data-no-loader') && 
            target.href && 
            !target.href.startsWith('#') &&
            !target.hasAttribute('download')) {
            
            isLinkClick = true; // Activamos la bandera antes de mostrar
            showLoader();
        }
    });
    
    // 2. Manejo de formularios
    document.addEventListener('submit', function (e) {
        const form = e.target;
        // Excepciones de formularios que no deben mostrar loader
        if (form.id === 'ventaForm' || form.hasAttribute('data-no-loader')) return;
        
        if (form.method.toLowerCase() === 'post' || form.hasAttribute('data-show-loader')) {
            showLoader();
        }
    });

    // 3. Interceptar todas las peticiones fetch
    const originalFetch = window.fetch;
    window.fetch = function (...args) {
        const [resource, config] = args;
        
        // No mostrar loader para solicitudes silenciosas o de precarga
        if (config?.headers?.['X-Silent'] || 
            resource.includes('preload') || 
            config?.headers?.['Preload']) {
            return originalFetch.apply(this, args);
        }
        
        showLoader();
        
        return originalFetch.apply(this, args)
            .then(response => {
                if (response.ok) {
                    // Esperar a que el cuerpo de la respuesta esté disponible
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

    // 4. Manejo de carga inicial de la página
    if (document.readyState === 'loading') {
        showLoader();
    }

    // 5. Eventos de carga de página
    window.addEventListener('load', function () {
        hideLoader();
    });

    // 6. Manejo de navegación por historial (adelante/atrás)
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            hideLoader();
        }
    });

    // 7. Manejo de recarga de página
    window.addEventListener('beforeunload', function () {
        showLoader();
    });

    // 8. Manejo de errores de carga de recursos
    window.addEventListener('error', function (e) {
        if (e.target && 
            (e.target.tagName === 'IMG' || 
             e.target.tagName === 'SCRIPT' || 
             e.target.tagName === 'LINK')) {
            hideLoader();
        }
    }, true);

    // 9. Manejo de carga de iframes
    document.querySelectorAll('iframe').forEach(iframe => {
        iframe.addEventListener('load', hideLoader);
        iframe.addEventListener('error', hideLoader);
    });

    // 10. Ocultar loader si todo está cargado muy rápido
    setTimeout(hideLoader, 2000); // Seguridad para evitar loader perpetuo
});