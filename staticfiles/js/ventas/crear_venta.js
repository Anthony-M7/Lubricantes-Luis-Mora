// Variables globales
const detallesData = [];
const emptyRow = document.getElementById("emptyRow");
const detallesBody = document.getElementById("detallesBody");
const finalizarBtn = document.getElementById("finalizarBtn");
const crearVentaForm = document.getElementById("crearVentaForm");

document.addEventListener("DOMContentLoaded", function () {
  // // Inicializar tooltips
  // const tooltipTriggerList = [].slice.call(
  //   document.querySelectorAll("[title]")
  // );
  // tooltipTriggerList.forEach(function (tooltipTriggerEl) {
  //   new bootstrap.Tooltip(tooltipTriggerEl);
  // });

  // Inicializar Select2 si existe
  // if ($().select2) {
  //   $(".select2").select2({
  //     placeholder: "Seleccione...",
  //     allowClear: true,
  //   });
  // }

  // Event listeners
  document
    .getElementById("buscarArticuloBtn")
    .addEventListener("click", function () {
      $("#buscarArticuloModal").modal("show");
    });

  // Delegación de eventos para los botones de agregar artículo
  document
    .getElementById("resultadosBusqueda")
    .addEventListener("click", function (e) {
      if (e.target.closest(".agregar-articulo")) {
        const articuloId = e.target.closest(".agregar-articulo").dataset.id;
        // Obtener los datos del artículo y mostrar el modal
        fetch(`/api/articulos/${articuloId}/`)
          .then((response) => response.json())
          .then((articulo) => {
            document.getElementById("articuloId").value = articulo.id;
            document.getElementById("cantidadInput").value = "1";
            document.getElementById("descuentoInput").value = "0";

            // Primero limpiamos los resultados y el campo de búsqueda
            document.getElementById("busquedaArticulo").value = ""; // Limpiar el input
            document.getElementById("resultadosBody").innerHTML = ""; // Limpiar los resultados

            // Luego ocultamos el modal
            $("#buscarArticuloModal").modal("hide");

            $("#cantidadModal").modal("show");
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("Error al obtener información del artículo");
          });
      }
    });

  document.getElementById("escanearBtn").addEventListener("click", function () {
    const codigo = document.getElementById("codigoBarrasInput").value.trim();
    if (codigo) buscarArticuloPorCodigo(codigo);
  });

  document
    .getElementById("buscarBtn")
    .addEventListener("click", buscarArticulos);
  document
    .getElementById("busquedaArticulo")
    .addEventListener("keypress", function (e) {
      if (e.key === "Enter") buscarArticulos();
    });

  document
    .getElementById("agregarArticuloBtn")
    .addEventListener("click", agregarArticulo);
  detallesBody.addEventListener("click", manejarClicksDetalles);
  crearVentaForm.addEventListener("submit", validarYEnviarFormulario);

  // Renderizar inicialmente
  renderizarDetalles();
});

// Funciones principales
function renderizarDetalles() {
  detallesBody.innerHTML = "";

  if (detallesData.length === 0 && emptyRow) {
    detallesBody.appendChild(emptyRow);
    return;
  }

  detallesData.forEach((detalle, index) => {
    const row = document.createElement("tr");
    row.dataset.index = index;
    row.innerHTML = `
      <td>${detalle.codigo}</td>
      <td>${detalle.descripcion}</td>
      <td>${parseFloat(detalle.stockActual).toFixed(3)}</td>
      <td>
        <input type="number" class="form-control cantidad-input" 
               value="${parseFloat(detalle.cantidad).toFixed(3)}" 
               min="0.001" step="0.001"
               max="${parseFloat(detalle.stockActual).toFixed(3)}">
      </td>
      <td>$${parseFloat(detalle.precio_unitario).toFixed(2)}</td>
      <td>$${parseFloat(detalle.descuento).toFixed(2)}</td>
      <td>$${parseFloat(detalle.subtotal).toFixed(2)}</td>
      <td class="text-end">
        <button type="button" class="btn btn-sm btn-outline-danger eliminar-detalle">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;

    // Agregar evento para cambiar cantidad
    row
      .querySelector(".cantidad-input")
      .addEventListener("change", function () {
        const nuevaCantidad = parseFloat(this.value);
        if (nuevaCantidad > detalle.stockActual) {
          alert(
            `No puede superar el stock disponible (${detalle.stockActual.toFixed(
              3
            )})`
          );
          this.value = detalle.cantidad.toFixed(3);
          return;
        }
        if (nuevaCantidad <= 0) {
          alert("La cantidad debe ser mayor que cero");
          this.value = detalle.cantidad.toFixed(3);
          return;
        }

        detalle.cantidad = nuevaCantidad;
        detalle.subtotal =
          detalle.precio_unitario * nuevaCantidad - detalle.descuento;
        renderizarDetalles();
      });

    detallesBody.appendChild(row);
  });

  actualizarTotales();
  actualizarBotonFinalizar();
}

function actualizarTotales() {
  let subtotal = 0;
  let impuesto = 0;

  detallesData.forEach((detalle) => {
    subtotal += detalle.subtotal;
    impuesto += detalle.impuesto;
  });

  const total = subtotal + impuesto;

  document.getElementById("subtotal").textContent = `COP ${subtotal.toFixed(
    2
  )}`;
  document.getElementById("impuestos").textContent = `COP ${impuesto.toFixed(
    2
  )}`;
  document.getElementById("total").textContent = `COP ${total.toFixed(2)}`;
}

function actualizarBotonFinalizar() {
  if (finalizarBtn) {
    finalizarBtn.disabled = detallesData.length === 0;
  }
}

function manejarClicksDetalles(e) {
  if (e.target.closest(".eliminar-detalle")) {
    const row = e.target.closest("tr");
    const index = parseInt(row.dataset.index);
    detallesData.splice(index, 1);
    renderizarDetalles();
  }
}

// Funciones de búsqueda y agregado de artículos
function buscarArticulos() {
  const query = document.getElementById("busquedaArticulo").value.trim();
  if (!query) return;

  fetch(`/ventas/buscar-articulos/?term=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => {
      const resultadosBody = document.getElementById("resultadosBody");
      resultadosBody.innerHTML = "";

      if (data.length === 0) {
        resultadosBody.innerHTML =
          '<tr><td colspan="5" class="text-center py-3">No se encontraron artículos</td></tr>';
        return;
      }

      data.forEach((articulo) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${articulo.codigo}</td>
          <td>${articulo.nombre}</td>
          <td>$${parseFloat(articulo.precio_venta).toFixed(2)}</td>
          <td>${parseFloat(articulo.stock_actual).toFixed(3)}</td>
          <td class="text-end">
            <button type="button" class="btn btn-sm btn-outline-primary agregar-articulo" 
                    data-id="${articulo.id}">
              <i class="bi bi-plus"></i> Agregar
            </button>
          </td>
        `;
        resultadosBody.appendChild(row);
      });
    })
    .catch((error) => {
      console.error("Error al buscar artículos:", error);
      alert("Error al buscar artículos");
    });
}

function buscarArticuloPorCodigo(codigo) {
  fetch(`/ventas/buscar-articulos/?term=${encodeURIComponent(codigo)}`)
    .then((response) => response.json())
    .then((data) => {
      if (data.length > 0) {
        mostrarModalCantidad(data[0]);
      } else {
        alert("Artículo no encontrado");
      }
    });
}

function agregarArticulo() {
  const articuloId = parseInt(document.getElementById("articuloId").value);
  const cantidad = parseFloat(document.getElementById("cantidadInput").value);
  const descuento =
    parseFloat(document.getElementById("descuentoInput").value) || 0;

  if (isNaN(cantidad) || cantidad <= 0) {
    alert("Ingrese una cantidad válida");
    return;
  }

  fetch(`/api/articulos/${articuloId}/?cantidad=${cantidad}&validar_stock=true`)
    .then((response) => {
      if (!response.ok) throw new Error("Error al obtener artículo");
      return response.json();
    })
    .then((articulo) => {
      if (articulo.error_stock) {
        alert(articulo.error_stock);
        return;
      }

      const precioUnitario = parseFloat(articulo.precio_venta);
      const subtotal = precioUnitario * cantidad - descuento;
      const impuesto = subtotal * (parseFloat(articulo.tasa_impuesto) / 100);

      // Verificar si el artículo ya está en la lista
      const indexExistente = detallesData.findIndex(
        (d) => d.articulo_id === articuloId
      );

      if (indexExistente >= 0) {
        // Actualizar si ya existe
        detallesData[indexExistente] = {
          ...detallesData[indexExistente],
          cantidad: cantidad,
          descuento: descuento,
          subtotal: subtotal,
          impuesto: impuesto,
        };
      } else {
        // Agregar nuevo artículo
        detallesData.push({
          articulo_id: articuloId,
          codigo: articulo.codigo,
          descripcion: articulo.nombre,
          cantidad: cantidad,
          stockActual: parseFloat(articulo.stock_actual),
          precio_unitario: precioUnitario,
          descuento: descuento,
          subtotal: subtotal,
          impuesto: impuesto,
          unidad_medida: articulo.unidad_medida || "",
        });
      }

      renderizarDetalles();
      $("#cantidadModal").modal("hide");
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Error al obtener información del artículo");
    });
}

function validarYEnviarFormulario(e) {
  e.preventDefault();

  // Validación básica
  if (detallesData.length === 0) {
    alert("Debe agregar al menos un artículo a la venta");
    return;
  }

  // Validación de stock y cantidades
  const errores = [];
  detallesData.forEach((art) => {
    if (art.cantidad <= 0) {
      errores.push(`La cantidad para ${art.descripcion} debe ser mayor que cero`);
    }
    if (art.cantidad > art.stockActual) {
      errores.push(`Stock insuficiente para ${art.descripcion} (disponible: ${art.stockActual})`);
    }
  });

  if (errores.length > 0) {
    alert(errores.join("\n"));
    return;
  }

  // Obtener el botón que disparó el envío
  const submitButton = document.activeElement;
  const isFinalizar = submitButton.name === 'finalizar_venta';

  // Crear FormData para asegurar el envío completo
  const formData = new FormData(crearVentaForm);
  
  // Agregar detalles y acción de botón
  formData.set('detalles', JSON.stringify(detallesData.map(art => ({
    articulo_id: art.articulo_id,
    cantidad: art.cantidad,
    descuento: art.descuento,
    precio_unitario: art.precio_unitario
  }))));

  // Asegurar que se envía el campo finalizar_venta
  if (isFinalizar) {
    formData.set('finalizar_venta', '1');
  }

  // Enviar mediante fetch para mejor control
  fetch(crearVentaForm.action, {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
    }
  })
  .then(response => {
    if (response.redirected) {
      window.location.href = response.url;
    } else {
      return response.json().then(data => {
        if (data.error) {
          alert(data.error);
        }
      });
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error al procesar la venta');
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("clienteForm");

  form.addEventListener("submit", function (e) {
    e.preventDefault(); // Evita recarga

    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        // 1. Obtener el select
        const clienteSelect = document.getElementById("id_cliente");

        // 2. Crear nueva opción
        const option = document.createElement("option");
        option.value = data.id;
        option.textContent = `${data.nombre} - ${data.identificacion}`;

        // 3. Agregarla al select y seleccionarla
        clienteSelect.appendChild(option);
        clienteSelect.value = data.id;

        // 4. Cerrar modal (si usas Bootstrap)
        const modal = bootstrap.Modal.getInstance(
          document.querySelector("#modalCliente")
        );
        modal.hide();

        // Opcional: limpiar el formulario
        form.reset();

        // También puedes insertar el cliente en una tabla o notificar al usuario
      })
      .catch((error) => {
        console.error("Error al crear el cliente:", error);
      });
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});

document.addEventListener("DOMContentLoaded", function() {
  const buscarClienteBtn = document.getElementById("buscarClienteBtn");
  const buscarClienteModalBtn = document.getElementById("buscarClienteModalBtn");
  const busquedaClienteInput = document.getElementById("busquedaCliente");
  const resultadosClienteBody = document.getElementById("resultadosClienteBody");
  const clienteSelect = document.getElementById("id_cliente"); // Asegúrate que este es el ID correcto
  
  // Abrir modal de búsqueda
  if (buscarClienteBtn) {
      buscarClienteBtn.addEventListener("click", function() {
          $("#buscarClienteModal").modal("show");
      });
  }
  
  // Función para buscar clientes
  function buscarClientes() {
      const query = busquedaClienteInput.value.trim();
      if (!query) {
          resultadosClienteBody.innerHTML = 
              '<tr><td colspan="4" class="text-center py-3">Ingrese un término de búsqueda</td></tr>';
          return;
      }
      
      fetch(`/api/clientes/buscar/?term=${encodeURIComponent(query)}`)
          .then(response => {
              if (!response.ok) throw new Error("Error en la respuesta del servidor");
              return response.json();
          })
          .then(data => {
              resultadosClienteBody.innerHTML = "";
              
              if (!data.results || data.results.length === 0) {
                  resultadosClienteBody.innerHTML = 
                      '<tr><td colspan="4" class="text-center py-3">No se encontraron clientes</td></tr>';
                  return;
              }
              
              data.results.forEach(cliente => {
                  const row = document.createElement("tr");
                  row.innerHTML = `
                      <td>${cliente.nombre}</td>
                      <td>${cliente.identificacion}</td>
                      <td>${cliente.telefono || ''}</td>
                      <td class="text-end">
                          <button type="button" class="btn btn-sm btn-outline-primary seleccionar-cliente" 
                                  data-id="${cliente.id}">
                              <i class="bi bi-check"></i> Seleccionar
                          </button>
                      </td>
                  `;
                  resultadosClienteBody.appendChild(row);
              });
          })
          .catch(error => {
              console.error("Error al buscar clientes:", error);
              resultadosClienteBody.innerHTML = 
                  '<tr><td colspan="4" class="text-center py-3 text-danger">Error al buscar clientes</td></tr>';
          });
  }
  
  // Eventos para buscar
  if (buscarClienteModalBtn) {
      buscarClienteModalBtn.addEventListener("click", buscarClientes);
  }
  
  if (busquedaClienteInput) {
      busquedaClienteInput.addEventListener("keypress", function(e) {
          if (e.key === "Enter") buscarClientes();
      });
  }
  
  // Seleccionar cliente
  if (resultadosClienteBody) {
      resultadosClienteBody.addEventListener("click", function(e) {
          if (e.target.closest(".seleccionar-cliente")) {
              const clienteId = e.target.closest(".seleccionar-cliente").dataset.id;
              seleccionarCliente(clienteId);
          }
      });
  }
  
  // Función para seleccionar cliente en el select
  function seleccionarCliente(clienteId) {
      if (!clienteSelect) return;
      
      // Verificar si el cliente existe en las opciones
      for (let option of clienteSelect.options) {
          if (option.value === clienteId) {
              clienteSelect.value = clienteId;
              
              // Si estás usando Select2
              if (typeof $ !== 'undefined' && $().select2) {
                  $(clienteSelect).trigger('change');
              }
              
              // Cerrar modal
              const modal = bootstrap.Modal.getInstance(document.getElementById("buscarClienteModal"));
              if (modal) modal.hide();
              
              return;
          }
      }
      
      // Si no se encontró el cliente en las opciones
      alert("No se pudo seleccionar el cliente. Por favor recargue la página.");
  }
});
