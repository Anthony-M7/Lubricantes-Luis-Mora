// Función para imprimir solo el contenido del modal
function printModalContent() {
  window.print();
}

document.addEventListener("DOMContentLoaded", function () {
  const modal = new bootstrap.Modal(document.getElementById("productModal"));

  document.querySelectorAll(".view-details").forEach((button) => {
    button.addEventListener("click", function () {
      const productId = this.getAttribute("data-product-id");

      // Mostrar loader
      document.getElementById("productModalBody").innerHTML = `
                <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                </div>
            `;

      modal.show();

      fetch(`/api/productos/${productId}/`)
        .then((response) => response.json())
        .then((data) => {
          // Construir el contenido del modal
          let htmlContent = `
    <div class="product-header">
        <div class="row align-items-center">
            <div class="col-md-3">
                ${
                  data.imagen
                    ? `<img src="${data.imagen}" alt="${data.nombre}" class="img-fluid rounded shadow">`
                    : '<div class="bg-light p-4 text-center text-muted rounded"><svg width="105px" height="105px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M3.17157 3.17157C2 4.34314 2 6.22876 2 9.99999V14C2 17.7712 2 19.6568 3.17157 20.8284C4.34315 22 6.22876 22 10 22H14C17.7712 22 19.6569 22 20.8284 20.8284C22 19.6569 22 17.7712 22 14V14V9.99999C22 7.16065 22 5.39017 21.5 4.18855V17C20.5396 17 19.6185 16.6185 18.9393 15.9393L18.1877 15.1877C17.4664 14.4664 17.1057 14.1057 16.6968 13.9537C16.2473 13.7867 15.7527 13.7867 15.3032 13.9537C14.8943 14.1057 14.5336 14.4664 13.8123 15.1877L13.6992 15.3008C13.1138 15.8862 12.8212 16.1788 12.5102 16.2334C12.2685 16.2758 12.0197 16.2279 11.811 16.0988C11.5425 15.9326 11.3795 15.5522 11.0534 14.7913L11 14.6667C10.2504 12.9175 9.87554 12.0429 9.22167 11.7151C8.89249 11.5501 8.52413 11.4792 8.1572 11.5101C7.42836 11.5716 6.75554 12.2445 5.40989 13.5901L3.5 15.5V2.88739C3.3844 2.97349 3.27519 3.06795 3.17157 3.17157Z" fill="#222222"></path> <path d="M3 10C3 8.08611 3.00212 6.75129 3.13753 5.74416C3.26907 4.76579 3.50966 4.2477 3.87868 3.87868C4.2477 3.50966 4.76579 3.26907 5.74416 3.13753C6.75129 3.00212 8.08611 3 10 3H14C15.9139 3 17.2487 3.00212 18.2558 3.13753C19.2342 3.26907 19.7523 3.50966 20.1213 3.87868C20.4903 4.2477 20.7309 4.76579 20.8625 5.74416C20.9979 6.75129 21 8.08611 21 10V14C21 15.9139 20.9979 17.2487 20.8625 18.2558C20.7309 19.2342 20.4903 19.7523 20.1213 20.1213C19.7523 20.4903 19.2342 20.7309 18.2558 20.8625C17.2487 20.9979 15.9139 21 14 21H10C8.08611 21 6.75129 20.9979 5.74416 20.8625C4.76579 20.7309 4.2477 20.4903 3.87868 20.1213C3.50966 19.7523 3.26907 19.2342 3.13753 18.2558C3.00212 17.2487 3 15.9139 3 14V10Z" stroke="#222222" stroke-width="2"></path> <circle cx="15" cy="9" r="2" fill="#222222"></circle> </g></svg><p class="mt-2">Sin imagen</p></div>'
                }
            </div>
            <div class="col-md-9">
                <h3 class="mb-2">${data.nombre}</h3>
                <div class="d-flex flex-wrap gap-2 mb-2">
                    <span class="badge bg-primary">${data.codigo}</span>
                    ${
                      data.codigo_barras
                        ? `<span class="badge bg-secondary">${data.codigo_barras}</span>`
                        : ""
                    }
                    ${
                      data.categoria
                        ? `<span class="badge bg-info text-dark">${data.categoria}</span>`
                        : ""
                    }
                    <span class="badge bg-dark">${data.unidad_medida}</span>
                    ${
                      data.necesita_reabastecimiento
                        ? '<span class="badge bg-danger stock-alert">Stock Bajo</span>'
                        : ""
                    }
                </div>
                <div class="d-flex align-items-center">
                    <h4 class="mb-0 me-3">$${data.precio_venta} COP</h4>
                    <small class="text-muted">Costo: $${
                      data.costo_promedio
                    } (Margen: ${data.margen_ganancia})</small>
                </div>
                </br>
                ${
                    data.codigo_barras
                      ? `
                  <div class="info-card">
                      <h5 class="text-primary"><i class="bi bi-upc-scan me-2"></i>Código de Barras</h5>
                      <div class="barcode-container text-center">
                          ${
                            data.barcode
                              ? `<img src="data:image/png;base64,${data.barcode}" alt="Código de barras" class="img-fluid">`
                              : ""
                          }
                          <p class="mt-2 mb-0 text-muted">${data.codigo_barras}</p>
                      </div>
                  </div>
                  `
                      : ""
                  }
            </div>
        </div>
    </div>
    
    <div class="row">
        <!-- Columna izquierda -->
        <div class="col-md-6">
            <div class="info-card">
                <h5 class="text-primary"><i class="bi bi-box-seam me-2"></i>Inventario</h5>
                <div class="row">
                    <div class="col-4">
                        <p class="mb-1"><strong>Stock Actual:</strong></p>
                        <h4 class="${
                          data.necesita_reabastecimiento
                            ? "text-danger"
                            : "text-success"
                        }">${data.stock_actual}</h4>
                    </div>
                    <div class="col-4">
                        <p class="mb-1"><strong>Mínimo:</strong></p>
                        <p>${data.stock_minimo}</p>
                    </div>
                    <div class="col-4">
                        <p class="mb-1"><strong>Máximo:</strong></p>
                        <p>${data.stock_maximo || "No Especificado"}</p>
                    </div>
                </div>
                <p class="mb-1"><strong>Valor Total Inventario:</strong> ${
                  data.valor_total
                } COP</p>
            </div>
            
            <div class="info-card">
                <h5 class="text-primary"><i class="bi bi-clock-history me-2"></i>Auditoría</h5>
                <p class="mb-1"><strong>Registrado por:</strong> ${
                  data.creado_por
                }</p>
                <p class="mb-1"><strong>Fecha creación:</strong> ${
                  data.fecha_creacion
                }</p>
                <p class="mb-1"><strong>Última actualización:</strong> ${
                  data.ultima_actualizacion || "No Modificado"
                }</p>
                <p class="mb-1"><strong>Estado:</strong> ${
                  data.activo
                    ? '<span class="badge bg-success">Activo</span>'
                    : '<span class="badge bg-secondary">Inactivo</span>'
                }</p>
            </div>
        </div>
        
        <!-- Columna derecha -->
        <div class="col-md-6">

            <div class="info-card">
                <h5 class="text-primary"><i class="bi bi-info-circle me-2"></i>Información Adicional</h5>

                <div class="row">
                    <div class="col-md-6">
                        ${
                          data.marca
                            ? `<p class="mb-1"><strong>Marca:</strong> ${data.marca}</p>`
                            : ""
                        }
                        ${
                          data.modelo
                            ? `<p class="mb-1"><strong>Modelo:</strong> ${data.modelo}</p>`
                            : ""
                        }
                        <p class="mb-1"><strong>Impuesto:</strong> ${
                          data.impuesto
                        }</p>
                    </div>

                    <div class="col-md-6">
                        ${
                          data.proveedor
                            ? `<p class="mb-1"><strong>Proveedor:</strong> ${data.proveedor}</p>`
                            : ""
                        }
                        <p class="mb-1"><strong>Tiempo reposición:</strong> ${
                          data.lead_time || "N/A"
                        } días</p>
                        <p class="mb-1"><strong>Registrado Por:</strong> ${
                          data.creado_por || "N/A"
                        }</p>
                    </div>

                    <div class="row-md-6">
                      <p class="mb-1"><strong>Descripción:</strong></p>
                      <p>${data.descripcion || "No hay descripción disponible"}</p>
                    
                      <p class="mb-1"><strong>Palabras Claves:</strong></p>
                      <p>${data.palabras_clave || "No hay Informacion disponible"}</p>
                    </div>

                    
                </div>
            </div>
            <!-- Nuevos campos para última compra y venta -->
            <div class="info-card">
            <h5 class="text-primary"><i class="bi bi-arrow-left-right"></i> Últimos Movimientos</h5>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Última compra:</strong></p>
                        <p>${data.ultima_compra ? `
                            ${data.ultima_compra.fecha}<br>
                            <small class="text-muted">${data.ultima_compra.cantidad} ${data.unidad_medida} · ${data.ultima_compra.precio_unitario} COP</small>
                        ` : 'N/A'}</p>
                    </div>
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Última venta:</strong></p>
                        <p>${data.ultima_venta ? `
                            ${data.ultima_venta.fecha}<br>
                            <small class="text-muted">${data.ultima_venta.cantidad} ${data.unidad_medida} · ${data.ultima_venta.precio_unitario} COP</small> </br>
                            <b class="text-muted">Total: ${data.ultima_venta.total} COP</b>
                        ` : 'N/A'}</p>
                    </div>
                </div>

            </div>
            
        </div>
    </div>
`;

          document.getElementById("productModalBody").innerHTML = htmlContent;
          document.getElementById(
            "productModalLabel"
          ).textContent = `${data.codigo} - ${data.nombre}`;
        })
        .catch((error) => {
          console.error("Error:", error);
          document.getElementById("productModalBody").innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle-fill"></i> No se pudieron cargar los detalles del producto.
                            <p class="mb-0 mt-2">${
                              error.message || "Error desconocido"
                            }</p>
                        </div>
                    `;
        });
    });
  });
});
