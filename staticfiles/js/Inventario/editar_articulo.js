document.addEventListener('DOMContentLoaded', function() {
    // Validación de precios
    const costoPromedio = document.getElementById('id_costo_promedio');
    const precioVenta = document.getElementById('id_precio_venta');
    
    function validarPrecios() {
        const costo = parseFloat(costoPromedio.value) || 0;
        const venta = parseFloat(precioVenta.value) || 0;
        
        if (venta < costo) {
            precioVenta.classList.add('is-invalid');
            return false;
        } else {
            precioVenta.classList.remove('is-invalid');
            return true;
        }
    }
    
    costoPromedio.addEventListener('change', validarPrecios);
    precioVenta.addEventListener('change', validarPrecios);
    
    // Validación de stock
    const stockActual = document.getElementById('id_stock_actual');
    const stockMinimo = document.getElementById('id_stock_minimo');
    const stockMaximo = document.getElementById('id_stock_maximo');
    
    function validarStock() {
        const actual = parseFloat(stockActual.value) || 0;
        const minimo = parseFloat(stockMinimo.value) || 0;
        const maximo = parseFloat(stockMaximo.value) || 0;
        
        let valido = true;
        
        if (minimo > actual) {
            stockMinimo.classList.add('is-invalid');
            valido = false;
        } else {
            stockMinimo.classList.remove('is-invalid');
        }
        
        if (maximo > 0 && minimo > maximo) {
            stockMinimo.classList.add('is-invalid');
            valido = false;
        }
        
        return valido;
    }
    
    stockActual.addEventListener('change', validarStock);
    stockMinimo.addEventListener('change', validarStock);
    stockMaximo.addEventListener('change', validarStock);
    
    // Validar formulario antes de enviar
    const form = document.getElementById('productForm');
    
    form.addEventListener('submit', function(e) {
        if (!validarPrecios() || !validarStock()) {
            e.preventDefault();
            
            // Mostrar mensaje de error
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger alert-dismissible fade show';
            alertDiv.innerHTML = `
                <strong>Error:</strong> Por favor corrige los errores en el formulario.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            const alertContainer = document.querySelector('.alert-container') || form;
            alertContainer.prepend(alertDiv);
            
            // Scroll a los errores
            const firstInvalid = form.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
    
    // Preview de imagen antes de subir
    const imagenInput = document.getElementById('id_imagen');
    if (imagenInput) {
        imagenInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    const preview = document.getElementById('imagePreview') || 
                        document.createElement('div');
                    preview.id = 'imagePreview';
                    preview.className = 'mt-2';
                    preview.innerHTML = `
                        <img src="${event.target.result}" class="img-thumbnail" 
                             style="max-height: 150px;" alt="Vista previa">
                    `;
                    
                    const container = imagenInput.parentElement;
                    const existingPreview = container.querySelector('#imagePreview');
                    if (existingPreview) {
                        existingPreview.replaceWith(preview);
                    } else {
                        container.appendChild(preview);
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
});