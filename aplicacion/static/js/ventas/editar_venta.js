document.addEventListener("DOMContentLoaded", function () {
  // Cargar detalles existentes
  const detallesData = JSON.parse(
    document.getElementById("detallesData").value
  );
  const detallesBody = document.getElementById("detallesBody");
  const emptyRow = document.getElementById("emptyRow");

  // Función para renderizar detalles
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
                <td>${parseFloat(detalle.cantidad).toFixed(3)}</td>
                <td>$${parseFloat(detalle.precio_unitario).toFixed(2)}</td>
                <td>$${parseFloat(detalle.descuento).toFixed(2)}</td>
                <td>$${parseFloat(detalle.subtotal).toFixed(2)}</td>
                <td class="text-end">
                    <button type="button" class="btn btn-sm btn-outline-danger eliminar-detalle">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
      detallesBody.appendChild(row);
    });

    actualizarTotales();
  }

  // Función para actualizar totales
  function actualizarTotales() {
    let subtotal = 0;
    let impuesto = 0;

    detallesData.forEach((detalle) => {
      subtotal += parseFloat(detalle.subtotal);
      impuesto += parseFloat(detalle.impuesto);
    });

    const total = subtotal + impuesto;

    document.getElementById("subtotal").textContent = `COP ${subtotal.toFixed(
      2
    )}`;
    document.getElementById("impuestos").textContent = `COP ${impuesto.toFixed(
      2
    )}`;
    document.getElementById("total").textContent = `COP ${total.toFixed(2)}`;

    // Habilitar botón de finalizar si hay artículos
    const finalizarBtn = document.getElementById("finalizarBtn");
    if (finalizarBtn) {
      finalizarBtn.disabled = detallesData.length === 0;
    }
  }

  // Eliminar detalle
  detallesBody.addEventListener("click", function (e) {
    if (e.target.closest(".eliminar-detalle")) {
      const row = e.target.closest("tr");
      const index = parseInt(row.dataset.index);

      detallesData.splice(index, 1);
      renderizarDetalles();
    }
  });

  // Buscar artículo (misma funcionalidad que en crear)
  document
    .getElementById("buscarArticuloBtn")
    .addEventListener("click", function () {
      $("#buscarArticuloModal").modal("show");
    });

  // Escanear código de barras (misma funcionalidad que en crear)
  document.getElementById("escanearBtn").addEventListener("click", function () {
    const codigo = document.getElementById("codigoBarrasInput").value.trim();
    if (codigo) {
      buscarArticuloPorCodigo(codigo);
    }
  });

  // Función para buscar artículo por código
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

  // Mostrar modal para agregar cantidad
  function mostrarModalCantidad(articulo) {
    // Primero limpiamos los resultados y el campo de búsqueda
    document.getElementById("busquedaArticulo").value = ""; // Limpiar el input
    document.getElementById("resultadosBody").innerHTML = ""; // Limpiar los resultados

    // Luego ocultamos el modal
    $("#buscarArticuloModal").modal("hide");

    document.getElementById("articuloId").value = articulo.id;
    document.getElementById("cantidadInput").value = "1";
    document.getElementById("descuentoInput").value = "0";
    $("#cantidadModal").modal("show");
  }

  document
    .getElementById("agregarArticuloBtn")
    .addEventListener("click", function () {
      const articuloId = parseInt(document.getElementById("articuloId").value);
      const cantidad = parseFloat(
        document.getElementById("cantidadInput").value
      );
      const descuento =
        parseFloat(document.getElementById("descuentoInput").value) || 0;

      if (isNaN(cantidad) || cantidad <= 0) {
        alert("Ingrese una cantidad válida");
        return;
      }

      // Buscar información completa del artículo con validación de stock
      fetch(
        `/api/articulos/${articuloId}/?cantidad=${cantidad}&validar_stock=true`
      )
        .then((response) => {
          if (!response.ok) {
            throw new Error("Error al obtener artículo");
          }
          return response.json();
        })
        .then((articulo) => {
          // Verificar si hay error de stock
          if (articulo.error_stock) {
            alert(articulo.error_stock);
            return;
          }

          // Calcular subtotal e impuesto
          const precioUnitario = parseFloat(articulo.precio_venta);
          const subtotal = precioUnitario * cantidad - descuento;
          const impuesto =
            subtotal * (parseFloat(articulo.tasa_impuesto) / 100);

          // Verificar si el artículo ya está en la lista
          const indexExistente = detallesData.findIndex(
            (d) => d.articulo_id === articuloId
          );

          if (indexExistente >= 0) {
            // Actualizar cantidad si ya existe
            detallesData[indexExistente].cantidad = cantidad;
            detallesData[indexExistente].descuento = descuento;
            detallesData[indexExistente].subtotal = subtotal;
            detallesData[indexExistente].impuesto = impuesto;
          } else {
            // Agregar nuevo artículo
            detallesData.push({
              articulo_id: articuloId,
              codigo: articulo.codigo,
              descripcion: articulo.nombre,
              cantidad: cantidad,
              precio_unitario: precioUnitario,
              descuento: descuento,
              subtotal: subtotal,
              impuesto: impuesto,
              unidad_medida: articulo.unidad_medida,
            });
          }

          renderizarDetalles();
          $("#cantidadModal").modal("hide");
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("Error al obtener información del artículo");
        });
    });

  document
    .getElementById("finalizarBtn")
    .addEventListener("click", function () {
      document.getElementById("finalizarVentaHidden").value = "1";
    });

  // Enviar formulario
  document.getElementById("ventaForm").addEventListener("submit", function (e) {
    e.preventDefault();

    // Agregar detalles al formulario antes de enviar
    const detallesInput = document.createElement("input");
    detallesInput.type = "hidden";
    detallesInput.name = "detalles";
    detallesInput.value = JSON.stringify(detallesData);
    this.appendChild(detallesInput);

    console.log("Detalles a enviar:", detallesData);

    this.submit();
  });

  // Inicializar
  renderizarDetalles();

  // Configurar búsqueda de artículos (misma funcionalidad que en crear)
  document
    .getElementById("buscarBtn")
    .addEventListener("click", buscarArticulos);
  document
    .getElementById("busquedaArticulo")
    .addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        buscarArticulos();
      }
    });

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
                        <td>$${parseFloat(articulo.precio_venta).toFixed(
                          2
                        )}</td>
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
      });
  }

  // Agregar artículo desde resultados de búsqueda
  document
    .getElementById("resultadosBusqueda")
    .addEventListener("click", function (e) {
      if (e.target.closest(".agregar-articulo")) {
        const articuloId = parseInt(
          e.target.closest(".agregar-articulo").dataset.id
        );
        $("#buscarArticuloModal").modal("hide");

        fetch(`/api/articulos/${articuloId}/`)
          .then((response) => response.json())
          .then((articulo) => {
            mostrarModalCantidad(articulo);
          });
      }
    });
});


document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('clienteForm');

  form.addEventListener('submit', function (e) {
    e.preventDefault(); // Evita recarga

    const formData = new FormData(form);

    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
    })
      .then(response => response.json())
      .then(data => {
        console.log('Cliente creado:', data); // 🎯 Aquí tienes los datos

        // 1. Obtener el select
        const clienteSelect = document.getElementById('id_cliente');

        // 2. Crear nueva opción
        const option = document.createElement('option');
        option.value = data.id;
        option.textContent = `${data.nombre} (${data.identificacion})`;

        // 3. Agregarla al select y seleccionarla
        clienteSelect.appendChild(option);
        clienteSelect.value = data.id;
        // Puedes usar `data.id`, `data.nombre`, etc.
        
        // Ejemplo: cerrar modal si estás usando Bootstrap
        const modal = bootstrap.Modal.getInstance(document.querySelector('#nuevoClienteModal'));
        modal.hide();

        // Opcional: limpiar el formulario
        form.reset();

        // También puedes insertar el cliente en una tabla o notificar al usuario
      })
      .catch(error => {
        console.error('Error al crear el cliente:', error);
      });
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});