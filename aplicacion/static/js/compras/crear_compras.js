document.addEventListener("DOMContentLoaded", function () {
  // Variables globales
  let ultimoNumeroRef = 0;

  // Generar referencia automática
  function generarReferencia() {
    const fecha = new Date();
    const fechaStr =
      fecha.getFullYear().toString().slice(-2) +
      ("0" + (fecha.getMonth() + 1)).slice(-2) +
      ("0" + fecha.getDate()).slice(-2);

    ultimoNumeroRef++;
    const numeroRef = ("00" + ultimoNumeroRef).slice(-3);

    const referencia = `COMPRA-${fechaStr}-${numeroRef}`;
    document.getElementById("id_referencia").value = referencia;
    document.querySelector(
      ".referencia-ayuda"
    ).textContent = `Referencia generada: ${referencia}`;
    validarCampo(document.getElementById("id_referencia"));
  }

  // Botón para generar referencia
  document
    .getElementById("generar-referencia")
    .addEventListener("click", generarReferencia);

  // Validar un campo específico con feedback individual
  function validarCampo(campo) {
    if (!campo) return false;

    const valor = campo.value.trim();
    const feedback = document.querySelector(`.${campo.id}-feedback`);

    // Resetear estados
    campo.classList.remove("is-valid", "is-invalid");
    if (feedback) feedback.style.display = "none";

    // Validaciones genéricas
    if (campo.required && !valor) {
      campo.classList.add("is-invalid");
      if (feedback) {
        feedback.textContent = "Este campo es obligatorio";
        feedback.style.display = "block";
      }
      return false;
    }

    // Validaciones específicas por campo
    switch (campo.id) {
      case "id_articulo":
        if (valor === "") {
          campo.classList.add("is-invalid");
          if (feedback) {
            feedback.textContent = "Debe seleccionar un artículo";
            feedback.style.display = "block";
          }
          return false;
        }
        break;

      case "id_cantidad":
        const cantidad = parseFloat(valor);

        if (isNaN(cantidad)) {
          campo.classList.add("is-invalid");
          if (feedback) {
            feedback.textContent = "Debe ingresar un número válido";
            feedback.style.display = "block";
          }
          return false;
        }

        if (cantidad <= 0) {
          campo.classList.add("is-invalid");
          if (feedback) {
            feedback.textContent = "La cantidad debe ser mayor a cero";
            feedback.style.display = "block";
          }
          return false;
        }
        break;

      case "id_costo_unitario":
        const precio = parseFloat(valor);
        if (isNaN(precio)) {
          campo.classList.add("is-invalid");
          if (feedback) {
            feedback.textContent = "Debe ingresar un número válido";
            feedback.style.display = "block";
          }
          return false;
        }
        if (precio <= 0) {
          campo.classList.add("is-invalid");
          if (feedback) {
            feedback.textContent = "El precio debe ser mayor a cero";
            feedback.style.display = "block";
          }
          return false;
        }
        break;

      case "id_referencia":
        if (valor.length < 5) {
          campo.classList.add("is-invalid");
          if (feedback) {
            feedback.textContent = "La referencia es demasiado corta";
            feedback.style.display = "block";
          }
          return false;
        }
        break;
    }

    // Si pasó todas las validaciones
    campo.classList.add("is-valid");
    return true;
  }
  // Calcular y mostrar total
  function calcularTotal() {
    const cantidad =
      parseFloat(document.getElementById("id_cantidad").value) || 0;
    const precio =
      parseFloat(document.getElementById("id_costo_unitario").value) || 0;
    const total = cantidad * precio;
    document.getElementById("total-compra").textContent =
      "COP " + total.toFixed(2);
    return total > 0;
  }

  // Calcular stock futuro
  function calcularStockFuturo() {
    const select = document.getElementById("id_articulo");
    const cantidad =
      parseFloat(document.getElementById("id_cantidad").value) || 0;
    const stockActual =
      parseFloat(select.options[select.selectedIndex]?.dataset.stock) || 0;
    const stockFuturo = stockActual + cantidad;
    document.getElementById("stock-futuro").textContent =
      stockFuturo.toFixed(2);
    return stockFuturo > 0;
  }

  // Validar todo el formulario
  function validarFormulario() {
    let valido = true;

    // Validar campos obligatorios
    valido = validarCampo(document.getElementById("id_articulo")) && valido;
    valido = validarCampo(document.getElementById("id_cantidad")) && valido;
    valido =
      validarCampo(document.getElementById("id_costo_unitario")) && valido;

    // Validar cálculos
    valido = calcularTotal() && valido;
    valido = calcularStockFuturo() && valido;

    // Actualizar estado (solo si el elemento existe)
    const estadoFormulario = document.getElementById("estado-formulario");
    const submitBtn = document.getElementById("submit-btn");

    if (estadoFormulario && submitBtn) {
      if (valido) {
        estadoFormulario.classList.remove("bg-warning");
        estadoFormulario.classList.add("bg-success");
        estadoFormulario.textContent = "Completo";
        submitBtn.disabled = false;
      } else {
        estadoFormulario.classList.remove("bg-success");
        estadoFormulario.classList.add("bg-warning");
        estadoFormulario.textContent = "Incompleto";
        submitBtn.disabled = true;
      }
    }

    return valido;
  }

  //   Cargar datos de artículos con Fetch
  function cargarArticulos() {
    fetch("/api/articulos/")
      .then((response) => response.json())
      .then((data) => {
        const select = document.getElementById("id_articulo");
        select.innerHTML =
          '<option value="" disabled selected>Seleccione un artículo</option>';

        data.forEach((articulo) => {
          const option = new Option();
          option.value = articulo.id;
          option.text = `${articulo.nombre}`;
          option.dataset.unidad = articulo.unidad_medida;
          option.dataset.stock = articulo.stock_actual;
          option.dataset.precio = articulo.costo_promedio;
          option.dataset.precio_venta = articulo.precio_venta;
          select.add(option);
        });
      })
      .catch((error) => {
        console.error("Error cargando artículos:", error);
        // Mostrar mensaje de error al usuario si es necesario
      });
  }

  // Actualizar resumen del artículo
  function actualizarResumenArticulo() {
    const select = document.getElementById("id_articulo");
    const articulo = select.options[select.selectedIndex].text;
    const resumenArticulo = document.getElementById("resumen-articulo");

    if (articulo && select.value) {
      resumenArticulo.textContent = articulo;

      // Actualizar unidad de medida
      const unidad =
        select.options[select.selectedIndex].dataset.unidad || "UN";
      const stock_actual =
        select.options[select.selectedIndex].dataset.stock || "UN";
      const precio_view =
        select.options[select.selectedIndex].dataset.precio || "UN";

      document.querySelectorAll(".unidad-medida").forEach((el) => {
        el.textContent = unidad;
      });
      //   document.getElementById("unidad-stock").textContent = unidad;
      document.getElementById("stock-actual").textContent = stock_actual;
      document.getElementById("precio-referencia").textContent =
        "COP " + parseInt(precio_view);
    } else {
      resumenArticulo.textContent = "No seleccionado";
    }
  }

  // Función para calcular y mostrar variación de precio
  function calcularVariacionPrecio() {
    const precioIngresado =
      parseFloat(document.getElementById("id_costo_unitario").value) || 0;
    const select = document.getElementById("id_articulo");
    const selectedOption = select.options[select.selectedIndex];

    if (!selectedOption || !selectedOption.value) return;

    const precioReferencia = parseFloat(selectedOption.dataset.precio) || 0;
    const variacionContainer = document.getElementById("variacion-precio");

    if (!variacionContainer) {
      console.error(
        "No se encontró el contenedor para mostrar la variación de precio"
      );
      return;
    }

    if (precioReferencia === 0) {
      variacionContainer.textContent = "No hay precio de referencia";
      variacionContainer.className = "text-muted";
      return;
    }

    const variacion =
      ((precioIngresado - precioReferencia) / precioReferencia) * 100;

    if (precioIngresado > precioReferencia) {
      variacionContainer.textContent = `↑ ${Math.abs(variacion).toFixed(
        2
      )}% más caro que la última compra`;
      variacionContainer.className = "text-danger";
    } else if (precioIngresado < precioReferencia) {
      variacionContainer.textContent = `↓ ${Math.abs(variacion).toFixed(
        2
      )}% más barato que la última compra`;
      variacionContainer.className = "text-success";
    } else {
      variacionContainer.textContent = "Mismo precio que la última compra";
      variacionContainer.className = "text-info";
    }
  }

  // Función para calcular y mostrar relación entre precio de compra y venta
  function compararPrecioCompraVenta() {
    const precioCompraIngresado =
      parseFloat(document.getElementById("id_costo_unitario").value) || 0;
    const select = document.getElementById("id_articulo");
    const selectedOption = select.options[select.selectedIndex];

    if (!selectedOption || !selectedOption.value) return;

    const precioVentaReferencia =
      parseFloat(selectedOption.dataset.precio_venta) || 0;
    const comparacionContainer = document.getElementById(
      "comparacion-precio-venta"
    );

    if (!comparacionContainer) {
      console.error(
        "No se encontró el contenedor para mostrar la comparación con precio de venta"
      );
      return;
    }

    if (precioVentaReferencia === 0) {
      comparacionContainer.textContent = "No hay precio de venta de referencia";
      comparacionContainer.className = "text-muted";
      return;
    }

    // Calcular diferencia absoluta y porcentaje
    const diferenciaAbsoluta = precioVentaReferencia - precioCompraIngresado;
    const margenPorcentaje =
      ((precioVentaReferencia - precioCompraIngresado) /
        precioCompraIngresado) *
      100;

    // Definir umbrales para los mensajes
    const umbralAlerta = 20; // Margen menor al 20% es preocupante
    const umbralAdvertencia = 30; // Margen menor al 30% es una advertencia

    if (precioCompraIngresado >= precioVentaReferencia) {
      comparacionContainer.textContent =
        "⚠️ Precio de compra IGUAL O MAYOR que precio de venta";
      comparacionContainer.className = "text-danger font-weight-bold";
    } else if (margenPorcentaje < umbralAlerta) {
      comparacionContainer.textContent = `⚠️ Margen muy bajo (${margenPorcentaje.toFixed(
        2
      )}%). Considere aumentar precio de venta`;
      comparacionContainer.className = "text-danger";
    } else if (margenPorcentaje < umbralAdvertencia) {
      comparacionContainer.textContent = `Margen bajo (${margenPorcentaje.toFixed(
        2
      )}%). Podría necesitar ajuste`;
      comparacionContainer.className = "text-warning";
    } else {
      comparacionContainer.textContent = `Margen saludable (${margenPorcentaje.toFixed(
        2
      )}%)`;
      comparacionContainer.className = "text-success";
    }
  }

  // Event listeners
  document
    .getElementById("id_articulo")
    .addEventListener("change", function () {
      actualizarResumenArticulo();
      validarFormulario();
      calcularVariacionPrecio(); // Añadimos esta línea
      compararPrecioCompraVenta();

      const option = this.options[this.selectedIndex];
      if (option.value) {
        document.querySelectorAll(".unidad-medida").forEach((el) => {
          el.textContent = option.dataset.unidad || "UN";
        });

        console.log(document.querySelectorAll(".unidad-medida"));
      }
    });

  document.getElementById("id_cantidad").addEventListener("input", function () {
    validarCampo(this);
    calcularTotal();
    validarFormulario();
    calcularStockFuturo();
  });

  document
    .getElementById("id_costo_unitario")
    .addEventListener("blur", function () {
      validarCampo(this);
      calcularTotal();

      validarFormulario();
      calcularVariacionPrecio(); // Añadimos esta línea
      compararPrecioCompraVenta();
    });

  document
    .getElementById("id_referencia")
    .addEventListener("input", function () {
      validarCampo(this);
      validarFormulario();
    });

  // Validar al enviar el formulario
  document
    .getElementById("compra-form")
    .addEventListener("submit", function (e) {
      if (!validarFormulario()) {
        e.preventDefault();
        e.stopPropagation();
      }
      this.classList.add("was-validated");
    });

  // Inicialización
  generarReferencia();
  validarFormulario();
  actualizarResumenArticulo();
  cargarArticulos();
});
