// Variables globales de la Venta / POS
const detallesData = [];

// Funciones Helper de Modales Tailwind
function abrirModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove("hidden");
}

function cerrarModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", function () {
  const emptyRow = document.getElementById("emptyRow");
  const detallesBody = document.getElementById("detallesBody");
  const finalizarBtn = document.getElementById("finalizarBtn");
  const crearVentaForm = document.getElementById("crearVentaForm");

  // Estilos Tailwind a los selects principales de Django
  const clienteSelect = document.getElementById("id_cliente");
  const metodoPagoSelect = document.getElementById("id_metodo_pago");
  const observacionesInput = document.getElementById("id_observaciones");

  if (clienteSelect) clienteSelect.className = "w-full py-2.5 px-3 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-brand-primary focus:bg-white transition";
  if (metodoPagoSelect) metodoPagoSelect.className = "w-full py-2.5 px-3 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-brand-primary focus:bg-white transition";
  if (observacionesInput) observacionesInput.className = "w-full py-2 px-3 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-brand-primary focus:bg-white transition";

  // Botón Abrir Búsqueda de Artículo
  const btnBuscarArticulo = document.getElementById("buscarArticuloBtn");
  if (btnBuscarArticulo) {
    btnBuscarArticulo.addEventListener("click", function () {
      abrirModal("buscarArticuloModal");
    });
  }

  // Delegación de eventos en tabla de resultados de búsqueda de artículos
  const tablaResultadosBusqueda = document.getElementById("resultadosBusqueda");
  if (tablaResultadosBusqueda) {
    tablaResultadosBusqueda.addEventListener("click", function (e) {
      const btnAgregar = e.target.closest(".agregar-articulo");
      if (btnAgregar) {
        const articuloId = btnAgregar.dataset.id;
        
        fetch(`/api/productos/${articuloId}/`)
          .then((res) => res.json())
          .then((articulo) => {
            document.getElementById("articuloId").value = articulo.id;
            document.getElementById("cantidadInput").value = "1";
            document.getElementById("descuentoInput").value = "0";

            document.getElementById("busquedaArticulo").value = "";
            document.getElementById("resultadosBody").innerHTML = "";

            cerrarModal("buscarArticuloModal");
            abrirModal("cantidadModal");
          })
          .catch((err) => {
            alert("Error al obtener información del artículo");
          });
      }
    });
  }

  // Escáner de Código de Barras
  const btnEscanear = document.getElementById("escanearBtn");
  if (btnEscanear) {
    btnEscanear.addEventListener("click", function () {
      const codigo = document.getElementById("codigoBarrasInput").value.trim();
      if (codigo) buscarArticuloPorCodigo(codigo);
    });
  }

  const inputCodigoBarras = document.getElementById("codigoBarrasInput");
  if (inputCodigoBarras) {
    inputCodigoBarras.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        const codigo = this.value.trim();
        if (codigo) buscarArticuloPorCodigo(codigo);
      }
    });
  }

  // Botón Buscar en Modal Artículos
  const btnBuscarModal = document.getElementById("buscarBtn");
  if (btnBuscarModal) btnBuscarModal.addEventListener("click", buscarArticulos);

  const inputBusquedaArt = document.getElementById("busquedaArticulo");
  if (inputBusquedaArt) {
    inputBusquedaArt.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        buscarArticulos();
      }
    });
  }

  // Agregar Artículo al Carrito
  const btnAgregarArt = document.getElementById("agregarArticuloBtn");
  if (btnAgregarArt) btnAgregarArt.addEventListener("click", agregarArticulo);

  // Clicks en Carrito (Eliminar)
  if (detallesBody) detallesBody.addEventListener("click", manejarClicksDetalles);

  // Submit del Formulario
  if (crearVentaForm) crearVentaForm.addEventListener("submit", validarYEnviarFormulario);

  // Modal Cliente Nuevo AJAX Submit
  const clienteForm = document.getElementById("clienteForm");
  if (clienteForm) {
    clienteForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const formData = new FormData(clienteForm);

      fetch(clienteForm.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
        },
      })
        .then((res) => res.json())
        .then((data) => {
          if (clienteSelect) {
            const option = document.createElement("option");
            option.value = data.id;
            option.textContent = `${data.nombre} - ${data.identificacion}`;
            option.selected = true;
            clienteSelect.appendChild(option);
            clienteSelect.value = data.id;
          }

          cerrarModal("modalCliente");
          clienteForm.reset();
        })
        .catch((err) => {
          alert("Error al guardar el cliente rápido");
        });
    });
  }

  // Modal Buscar Cliente
  const btnAbrirBuscarCliente = document.getElementById("buscarClienteBtn");
  if (btnAbrirBuscarCliente) {
    btnAbrirBuscarCliente.addEventListener("click", function () {
      abrirModal("buscarClienteModal");
    });
  }

  const btnBuscarClienteModal = document.getElementById("buscarClienteModalBtn");
  if (btnBuscarClienteModal) btnBuscarClienteModal.addEventListener("click", buscarClientes);

  const inputBusquedaCliente = document.getElementById("busquedaCliente");
  if (inputBusquedaCliente) {
    inputBusquedaCliente.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        buscarClientes();
      }
    });
  }

  const tablaResultadosCliente = document.getElementById("resultadosClienteBody");
  if (tablaResultadosCliente) {
    tablaResultadosCliente.addEventListener("click", function (e) {
      const btnSel = e.target.closest(".seleccionar-cliente");
      if (btnSel) {
        const clienteId = btnSel.dataset.id;
        seleccionarCliente(clienteId);
      }
    });
  }

  // Render inicial
  renderizarDetalles();
});

// Renderizar Carrito de Venta
function renderizarDetalles() {
  const detallesBody = document.getElementById("detallesBody");
  const emptyRow = document.getElementById("emptyRow");
  if (!detallesBody) return;

  detallesBody.innerHTML = "";

  if (detallesData.length === 0) {
    detallesBody.innerHTML = `
      <tr id="emptyRow">
        <td colspan="8" class="py-12 text-center text-slate-400 font-medium">
          <i class="bi bi-cart-x text-3xl block text-slate-300 mb-2"></i>
          No hay artículos agregados. Usa el buscador o escáner para agregar productos.
        </td>
      </tr>
    `;
    actualizarTotales();
    actualizarBotonFinalizar();
    return;
  }

  detallesData.forEach((detalle, index) => {
    const row = document.createElement("tr");
    row.dataset.index = index;
    row.className = "hover:bg-slate-50 transition border-b border-slate-100";
    row.innerHTML = `
      <td class="px-4 py-3 font-mono font-bold text-slate-700 whitespace-nowrap">${detalle.codigo}</td>
      <td class="px-4 py-3 font-bold text-slate-900 min-w-[250px] whitespace-nowrap overflow-hidden text-ellipsis max-w-[300px]">${detalle.descripcion}</td>
      <td class="px-4 py-3 text-center font-semibold text-slate-600 whitespace-nowrap">${parseFloat(detalle.stockActual)}</td>
      <td class="px-4 py-3 w-28 text-center whitespace-nowrap">
        <input type="number" class="cantidad-input w-20 py-1 px-2 text-center bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold text-slate-900 focus:ring-2 focus:ring-brand-primary" 
               value="${parseFloat(detalle.cantidad)}" 
               min="0.1" step="0.1"
               max="${parseFloat(detalle.stockActual)}">
      </td>
      <td class="px-4 py-3 text-right font-semibold text-slate-700 whitespace-nowrap">COP ${parseFloat(detalle.precio_unitario).toLocaleString("es-CO")}</td>
      <td class="px-4 py-3 text-right font-semibold text-rose-600 whitespace-nowrap">COP ${parseFloat(detalle.descuento).toLocaleString("es-CO")}</td>
      <td class="px-4 py-3 text-right font-black text-emerald-600 whitespace-nowrap">COP ${parseFloat(detalle.subtotal).toLocaleString("es-CO")}</td>
      <td class="px-4 py-3 text-center whitespace-nowrap">
        <button type="button" class="eliminar-detalle p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg transition" title="Quitar">
          <i class="bi bi-trash text-sm"></i>
        </button>
      </td>
    `;

    // Modificar Cantidad en vivo
    row.querySelector(".cantidad-input").addEventListener("change", function () {
      const nuevaCantidad = parseFloat(this.value);
      if (nuevaCantidad > detalle.stockActual) {
        alert(`La cantidad no puede superar el stock disponible (${detalle.stockActual})`);
        this.value = detalle.cantidad;
        return;
      }
      if (nuevaCantidad <= 0 || isNaN(nuevaCantidad)) {
        alert("La cantidad debe ser mayor a cero");
        this.value = detalle.cantidad;
        return;
      }

      detalle.cantidad = nuevaCantidad;
      detalle.subtotal = (detalle.precio_unitario * nuevaCantidad) - detalle.descuento;
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
    impuesto += detalle.impuesto || 0;
  });

  const total = subtotal + impuesto;

  const subtotalElem = document.getElementById("subtotal");
  const impuestosElem = document.getElementById("impuestos");
  const totalElem = document.getElementById("total");

  if (subtotalElem) subtotalElem.textContent = `COP ${subtotal.toLocaleString("es-CO", { minimumFractionDigits: 2 })}`;
  if (impuestosElem) impuestosElem.textContent = `COP ${impuesto.toLocaleString("es-CO", { minimumFractionDigits: 2 })}`;
  if (totalElem) totalElem.textContent = `COP ${total.toLocaleString("es-CO", { minimumFractionDigits: 2 })}`;
}

function actualizarBotonFinalizar() {
  const finalizarBtn = document.getElementById("finalizarBtn");
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

// Búsqueda de Artículos API
function buscarArticulos() {
  const query = document.getElementById("busquedaArticulo").value.trim();
  if (!query) return;

  fetch(`/ventas/buscar-articulos/?term=${encodeURIComponent(query)}`)
    .then((res) => res.json())
    .then((data) => {
      const resultadosBody = document.getElementById("resultadosBody");
      if (!resultadosBody) return;

      resultadosBody.innerHTML = "";

      if (data.length === 0) {
        resultadosBody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-slate-400">No se encontraron artículos</td></tr>';
        return;
      }

      data.forEach((art) => {
        const row = document.createElement("tr");
        row.className = "hover:bg-slate-50 transition border-b border-slate-100";
        row.innerHTML = `
          <td class="px-4 py-3 font-mono font-bold text-slate-700">${art.codigo}</td>
          <td class="px-4 py-3 font-bold text-slate-900">${art.nombre}</td>
          <td class="px-4 py-3 font-semibold text-slate-800">COP ${parseFloat(art.precio_venta).toLocaleString("es-CO")}</td>
          <td class="px-4 py-3 text-center font-bold ${art.stock_actual <= 0 ? 'text-rose-600' : 'text-emerald-600'}">${parseFloat(art.stock_actual)}</td>
          <td class="px-4 py-3 text-right">
            <button type="button" class="agregar-articulo px-3 py-1.5 bg-brand-primary hover:bg-brand-dark text-white font-bold text-xs rounded-lg transition" data-id="${art.id}">
              <i class="bi bi-plus"></i> Agregar
            </button>
          </td>
        `;
        resultadosBody.appendChild(row);
      });
    })
    .catch(() => {
      alert("Error al buscar artículos");
    });
}

function buscarArticuloPorCodigo(codigo) {
  fetch(`/ventas/buscar-articulos/?term=${encodeURIComponent(codigo)}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.length > 0) {
        const art = data[0];
        document.getElementById("articuloId").value = art.id;
        document.getElementById("cantidadInput").value = "1";
        document.getElementById("descuentoInput").value = "0";
        abrirModal("cantidadModal");
      } else {
        alert("Artículo no encontrado para ese código de barras");
      }
    });
}

function agregarArticulo() {
  const articuloId = parseInt(document.getElementById("articuloId").value);
  const cantidad = parseFloat(document.getElementById("cantidadInput").value);
  const descuento = parseFloat(document.getElementById("descuentoInput").value) || 0;

  if (isNaN(cantidad) || cantidad <= 0) {
    alert("Ingrese una cantidad válida");
    return;
  }

  fetch(`/api/productos/${articuloId}/`)
    .then((res) => {
      if (!res.ok) throw new Error("Error al obtener artículo");
      return res.json();
    })
    .then((articulo) => {
      const stockDisp = parseFloat(articulo.stock_actual);
      if (cantidad > stockDisp) {
        alert(`Stock insuficiente. Solo hay ${stockDisp} disponibles en inventario.`);
        return;
      }

      const precioUnitario = parseFloat(articulo.precio_venta);
      const subtotal = (precioUnitario * cantidad) - descuento;
      const tasaImpuesto = parseFloat(articulo.tasa_impuesto) || 0;
      const impuesto = 0; // Sin impuesto por solicitud del cliente

      const indexExistente = detallesData.findIndex((d) => d.articulo_id === articuloId);

      if (indexExistente >= 0) {
        detallesData[indexExistente] = {
          ...detallesData[indexExistente],
          cantidad: cantidad,
          descuento: descuento,
          subtotal: subtotal,
          impuesto: impuesto,
        };
      } else {
        detallesData.push({
          articulo_id: articuloId,
          codigo: articulo.codigo,
          descripcion: articulo.nombre,
          cantidad: cantidad,
          stockActual: stockDisp,
          precio_unitario: precioUnitario,
          descuento: descuento,
          subtotal: subtotal,
          impuesto: impuesto,
          unidad_medida: articulo.unidad_medida || "",
        });
      }

      renderizarDetalles();
      cerrarModal("cantidadModal");
    })
    .catch(() => {
      alert("Error al obtener información del artículo");
    });
}

function validarYEnviarFormulario(e) {
  e.preventDefault();

  if (detallesData.length === 0) {
    alert("Debe agregar al menos un artículo a la venta");
    return;
  }

  const crearVentaForm = document.getElementById("crearVentaForm");
  const submitButton = document.activeElement;
  const isFinalizar = submitButton && submitButton.name === "finalizar_venta";

  const formData = new FormData(crearVentaForm);
  
  formData.set("detalles", JSON.stringify(detallesData.map(art => ({
    articulo_id: art.articulo_id,
    cantidad: art.cantidad,
    descuento: art.descuento,
    precio_unitario: art.precio_unitario
  }))));

  if (isFinalizar) {
    formData.set("finalizar_venta", "1");
  }

  fetch(crearVentaForm.action || window.location.href, {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
    }
  })
  .then(response => {
    if (response.redirected) {
      window.location.href = response.url;
    } else {
      return response.json().then(data => {
        if (data.error) {
          alert(data.error);
        } else if (data.redirect_url) {
          window.location.href = data.redirect_url;
        }
      });
    }
  })
  .catch(() => {
    alert("Error al procesar la venta");
  });
}

function buscarClientes() {
  const busquedaClienteInput = document.getElementById("busquedaCliente");
  const resultadosClienteBody = document.getElementById("resultadosClienteBody");
  if (!busquedaClienteInput || !resultadosClienteBody) return;

  const query = busquedaClienteInput.value.trim();
  if (!query) return;

  fetch(`/api/clientes/buscar/?term=${encodeURIComponent(query)}`)
    .then((res) => res.json())
    .then((data) => {
      resultadosClienteBody.innerHTML = "";
      const lista = data.results || data;

      if (!lista || lista.length === 0) {
        resultadosClienteBody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-slate-400">No se encontraron clientes</td></tr>';
        return;
      }

      lista.forEach((cliente) => {
        const row = document.createElement("tr");
        row.className = "hover:bg-slate-50 transition border-b border-slate-100";
        row.innerHTML = `
          <td class="px-4 py-3 font-bold text-slate-900">${cliente.nombre}</td>
          <td class="px-4 py-3 font-mono text-slate-700">${cliente.identificacion}</td>
          <td class="px-4 py-3 text-slate-600">${cliente.telefono || 'N/A'}</td>
          <td class="px-4 py-3 text-right">
            <button type="button" class="seleccionar-cliente px-3 py-1.5 bg-brand-primary hover:bg-brand-dark text-white font-bold text-xs rounded-lg transition" data-id="${cliente.id}">
              Seleccionar
            </button>
          </td>
        `;
        resultadosClienteBody.appendChild(row);
      });
    })
    .catch(() => {
      resultadosClienteBody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-rose-600">Error al buscar clientes</td></tr>';
    });
}

function seleccionarCliente(clienteId) {
  const clienteSelect = document.getElementById("id_cliente");
  if (!clienteSelect) return;

  for (let option of clienteSelect.options) {
    if (String(option.value) === String(clienteId)) {
      clienteSelect.value = clienteId;
      cerrarModal("buscarClienteModal");
      return;
    }
  }

  alert("No se pudo seleccionar el cliente en la lista.");
}
