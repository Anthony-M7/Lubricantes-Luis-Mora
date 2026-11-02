// Función para imprimir el contenido del modal de producto
function printModalContent() {
  window.print();
}

document.addEventListener("DOMContentLoaded", function () {
  const modalElem = document.getElementById("productModal");
  const modalBody = document.getElementById("productModalBody");
  const modalTitle = document.getElementById("productModalLabel");

  document.querySelectorAll(".view-details").forEach((button) => {
    button.addEventListener("click", function () {
      const productId = this.getAttribute("data-product-id");

      if (!modalElem || !modalBody) return;

      // Mostrar Spinner con estilo Tailwind
      modalBody.innerHTML = `
        <div class="flex flex-col items-center justify-center py-16 space-y-4">
          <div class="w-12 h-12 border-4 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Cargando detalles del producto...</p>
        </div>
      `;

      // Mostrar Modal (Tailwind hidden toggle)
      modalElem.classList.remove("hidden");

      fetch(`/api/productos/${productId}/`)
        .then((response) => {
          if (!response.ok) throw new Error("Error en la respuesta del servidor");
          return response.json();
        })
        .then((data) => {
          if (modalTitle) {
            modalTitle.innerHTML = `
              <i class="bi bi-box-seam text-sky-400 me-2"></i>
              <span>${data.codigo || ''} - ${data.nombre}</span>
            `;
          }

          // Generar Badges de Estado y Categoría
          const stockStatusBg = data.stock_actual <= 0 
            ? 'bg-rose-100 text-rose-800 border-rose-200' 
            : (data.necesita_reabastecimiento ? 'bg-amber-100 text-amber-800 border-amber-200' : 'bg-emerald-100 text-emerald-800 border-emerald-200');
          
          const stockStatusText = data.stock_actual <= 0 
            ? 'Agotado' 
            : (data.necesita_reabastecimiento ? 'Stock Bajo (Alerta)' : 'Disponible');

          // Generar Palabras Clave / Tags
          let tagsHtml = '';
          if (data.palabras_clave) {
            tagsHtml = data.palabras_clave.split(',').map(tag => 
              `<span class="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200">${tag.trim()}</span>`
            ).join(' ');
          }

          // HTML Completo con TailwindCSS
          let htmlContent = `
            <div class="space-y-6">
              
              <!-- Cabecera Principal del Producto -->
              <div class="grid grid-cols-1 md:grid-cols-12 gap-6 bg-slate-50 p-5 rounded-2xl border border-slate-200">
                <!-- Imagen -->
                <div class="md:col-span-4 bg-white p-3 rounded-2xl border border-slate-200 flex items-center justify-center min-h-[220px]">
                  ${
                    data.imagen
                      ? `<img src="${data.imagen}" alt="${data.nombre}" class="max-h-56 max-w-full object-contain rounded-xl drop-shadow-md">`
                      : `<div class="flex flex-col items-center justify-center text-slate-400 py-8">
                           <i class="bi bi-image text-5xl"></i>
                           <span class="text-xs font-semibold mt-2">Sin Fotografía</span>
                         </div>`
                  }
                </div>

                <!-- Info Clave -->
                <div class="md:col-span-8 space-y-4 flex flex-col justify-between">
                  <div>
                    <div class="flex flex-wrap items-center gap-2 mb-2">
                      <span class="px-3 py-1 bg-brand-primary/10 text-brand-dark text-xs font-bold rounded-lg border border-brand-primary/20">
                        Código: ${data.codigo}
                      </span>
                      ${
                        data.codigo_barras
                          ? `<span class="px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-lg border border-emerald-200 flex items-center gap-1">
                              <i class="bi bi-upc-scan me-1"></i> ${data.codigo_barras}
                             </span>`
                          : ''
                      }
                      <span class="px-3 py-1 text-xs font-bold rounded-lg border ${stockStatusBg}">
                        ${stockStatusText}
                      </span>
                    </div>

                    <h2 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight leading-snug mb-1">
                      ${data.nombre}
                    </h2>

                    <div class="flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-500 mb-3">
                      ${data.marca ? `<span>Marca: <strong class="text-slate-800">${data.marca}</strong></span>` : ''}
                      ${data.modelo ? `<span>• Modelo: <strong class="text-slate-800">${data.modelo}</strong></span>` : ''}
                      ${data.categoria ? `<span>• Categoría: <strong class="text-brand-primary">${data.categoria}</strong></span>` : ''}
                      ${data.unidad_medida ? `<span>• Medida: <strong class="text-slate-800">${data.unidad_medida}</strong></span>` : ''}
                    </div>

                    <p class="text-xs text-slate-600 leading-relaxed bg-white p-3 rounded-xl border border-slate-200/80">
                      ${data.descripcion || 'Sin descripción adicional registrada.'}
                    </p>
                  </div>

                  <!-- Precio y Margen -->
                  <div class="flex flex-col sm:flex-row sm:items-center justify-between bg-white p-4 rounded-xl border border-slate-200 gap-2">
                    <div>
                      <span class="text-[11px] font-bold uppercase text-slate-400 tracking-wider">Precio de Venta al Público</span>
                      <div class="text-2xl font-black text-emerald-600">
                        COP ${data.precio_venta}
                      </div>
                    </div>
                    <div class="text-right sm:border-l sm:border-slate-100 sm:pl-4">
                      <span class="text-[11px] font-semibold text-slate-500 block">Costo Promedio: COP ${data.costo_promedio}</span>
                      <span class="text-xs font-bold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-md border border-sky-200 inline-block mt-0.5">
                        Margen de Ganancia: ${data.margen_ganancia || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Fórmulas y Secciones Detalladas -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                <!-- Columna Izquierda: Control de Inventario -->
                <div class="space-y-4">
                  <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                    <h4 class="text-xs font-bold uppercase text-brand-dark tracking-wider flex items-center gap-2 pb-2 border-b border-slate-100">
                      <i class="bi bi-box-seam text-brand-primary text-base"></i>
                      <span>Control de Inventario y Stock</span>
                    </h4>

                    <div class="grid grid-cols-3 gap-3 text-center">
                      <div class="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span class="text-[10px] font-bold text-slate-500 uppercase block">Actual</span>
                        <span class="text-lg font-black ${data.necesita_reabastecimiento ? 'text-rose-600' : 'text-emerald-600'}">
                          ${data.stock_actual}
                        </span>
                      </div>

                      <div class="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span class="text-[10px] font-bold text-slate-500 uppercase block">Mínimo</span>
                        <span class="text-lg font-bold text-slate-700">${data.stock_minimo || 3}</span>
                      </div>

                      <div class="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span class="text-[10px] font-bold text-slate-500 uppercase block">Máximo</span>
                        <span class="text-lg font-bold text-slate-700">${data.stock_maximo || 12}</span>
                      </div>
                    </div>

                    <div class="flex items-center justify-between text-xs font-semibold text-slate-600 pt-2 border-t border-slate-100">
                      <span>Valor Total del Inventario:</span>
                      <strong class="text-slate-900 font-bold">COP ${data.valor_total || '0.00'}</strong>
                    </div>
                  </div>

                  <!-- Auditoría y Estado -->
                  <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2 text-xs">
                    <h4 class="font-bold uppercase text-brand-dark tracking-wider flex items-center gap-2 pb-2 border-b border-slate-100 text-[11px]">
                      <i class="bi bi-clock-history text-sky-600 text-base"></i>
                      <span>Registro y Auditoría</span>
                    </h4>
                    <div class="flex justify-between">
                      <span class="text-slate-500">Registrado Por:</span>
                      <span class="font-bold text-slate-800">${data.creado_por || 'Sistema'}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-slate-500">Fecha de Creación:</span>
                      <span class="font-medium text-slate-800">${data.fecha_creacion || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-slate-500">Proveedor Principal:</span>
                      <span class="font-bold text-slate-800">${data.proveedor || 'No asignado'}</span>
                    </div>
                  </div>
                </div>

                <!-- Columna Derecha: Movimientos y Palabras Clave -->
                <div class="space-y-4">
                  <!-- Úlitmos Movimientos -->
                  <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                    <h4 class="text-xs font-bold uppercase text-brand-dark tracking-wider flex items-center gap-2 pb-2 border-b border-slate-100">
                      <i class="bi bi-arrow-left-right text-amber-500 text-base"></i>
                      <span>Últimos Movimientos</span>
                    </h4>

                    <div class="grid grid-cols-2 gap-3 text-xs">
                      <div class="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <span class="font-bold text-slate-700 block mb-1">Última Compra</span>
                        ${
                          data.ultima_compra
                            ? `<span class="text-slate-500 block">${data.ultima_compra.fecha}</span>
                               <span class="font-bold text-emerald-600">${data.ultima_compra.cantidad} ${data.unidad_medida} @ COP ${data.ultima_compra.precio_unitario}</span>`
                            : `<span class="text-slate-400 italic">Sin registros</span>`
                        }
                      </div>

                      <div class="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <span class="font-bold text-slate-700 block mb-1">Última Venta</span>
                        ${
                          data.ultima_venta
                            ? `<span class="text-slate-500 block">${data.ultima_venta.fecha}</span>
                               <span class="font-bold text-sky-600">${data.ultima_venta.cantidad} ${data.unidad_medida} @ COP ${data.ultima_venta.precio_unitario}</span>`
                            : `<span class="text-slate-400 italic">Sin registros</span>`
                        }
                      </div>
                    </div>
                  </div>

                  <!-- Etiquetas y Palabras Clave -->
                  <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
                    <h4 class="text-xs font-bold uppercase text-brand-dark tracking-wider flex items-center gap-2 pb-2 border-b border-slate-100">
                      <i class="bi bi-tags text-indigo-500 text-base"></i>
                      <span>Compatibilidad y Palabras Clave</span>
                    </h4>
                    <div class="flex flex-wrap gap-1.5 pt-1">
                      ${tagsHtml || '<span class="text-xs text-slate-400 italic">No hay palabras clave asignadas</span>'}
                    </div>
                  </div>
                </div>

              </div>

              <!-- Pie Acciones Rápidas Modal -->
              <div class="flex items-center justify-between pt-4 border-t border-slate-200">
                <a href="/articulos/editar/${data.id}/" class="px-4 py-2 bg-brand-primary hover:bg-brand-dark text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-2">
                  <i class="bi bi-pencil"></i>
                  <span>Editar este Producto</span>
                </a>

                <div class="flex items-center space-x-2">
                  <button type="button" onclick="document.getElementById('productModal').classList.add('hidden')" class="px-5 py-2 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs rounded-xl transition">
                    Cerrar
                  </button>
                </div>
              </div>

            </div>
          `;

          modalBody.innerHTML = htmlContent;
        })
        .catch((error) => {
          console.error("Error al cargar producto:", error);
          modalBody.innerHTML = `
            <div class="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-center space-y-2">
              <i class="bi bi-exclamation-triangle-fill text-3xl text-rose-600 block"></i>
              <h4 class="font-bold text-sm">No se pudieron cargar los detalles del producto</h4>
              <p class="text-xs text-rose-600">${error.message || 'Error de conexión'}</p>
            </div>
          `;
        });
    });
  });
});
