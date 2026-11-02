document.addEventListener("DOMContentLoaded", function () {
  let ultimoNumeroRef = 0;
  let articulosCache = [];

  // Referencias a Elementos DOM
  const selectArticulo = document.getElementById("id_articulo");
  const inputFiltroArticulo = document.getElementById("buscar-articulo-filtro");
  const selectProveedor = document.getElementById("id_proveedor");
  const inputCantidad = document.getElementById("id_cantidad");
  const inputCostoUnitario = document.getElementById("id_costo_unitario");
  const inputReferencia = document.getElementById("id_referencia");
  const btnGenerarRef = document.getElementById("generar-referencia");
  const submitBtn = document.getElementById("submit-btn");
  const estadoFormulario = document.getElementById("estado-formulario");

  // Elementos del Resumen Financiero
  const imgArticulo = document.getElementById("imagen-articulo");
  const imgPlaceholder = document.getElementById("imagen-placeholder");
  const resumenArticuloText = document.getElementById("resumen-articulo");
  const categoriaBadge = document.getElementById("categoria-resumen-badge");
  const stockActualText = document.getElementById("stock-actual");
  const stockFuturoText = document.getElementById("stock-futuro");
  const precioReferenciaText = document.getElementById("precio-referencia");
  const nuevoCppText = document.getElementById("nuevo-cpp-proyectado");
  const variacionPrecioDiv = document.getElementById("variacion-precio");
  const comparacionVentaDiv = document.getElementById("comparacion-precio-venta");
  const totalCompraText = document.getElementById("total-compra");

  // Estilos Tailwind para los campos del formulario
  if (selectArticulo) selectArticulo.className = "w-full py-2.5 px-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-brand-primary focus:bg-white transition";
  if (selectProveedor) selectProveedor.className = "w-full py-2.5 px-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-brand-primary focus:bg-white transition";
  if (inputCantidad) inputCantidad.className = "w-full py-2.5 px-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-bold text-slate-900 focus:ring-2 focus:ring-brand-primary focus:bg-white transition";
  if (inputCostoUnitario) inputCostoUnitario.className = "w-full py-2.5 px-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-bold text-emerald-700 focus:ring-2 focus:ring-brand-primary focus:bg-white transition";
  if (inputReferencia) inputReferencia.className = "w-full py-2.5 px-3 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-brand-primary focus:bg-white transition";
  
  const inputObs = document.getElementById("id_observaciones");
  if (inputObs) inputObs.className = "w-full py-2 px-3 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium focus:ring-2 focus:ring-brand-primary focus:bg-white transition";

  // Generar Referencia Única de Factura / Remisión
  function generarReferencia() {
    const fecha = new Date();
    const fechaStr =
      fecha.getFullYear().toString().slice(-2) +
      ("0" + (fecha.getMonth() + 1)).slice(-2) +
      ("0" + fecha.getDate()).slice(-2);

    ultimoNumeroRef++;
    const numeroRef = ("00" + ultimoNumeroRef).slice(-3);
    const referencia = `CMP-${fechaStr}-${numeroRef}`;

    if (inputReferencia) {
      inputReferencia.value = referencia;
    }
    const ayudaRef = document.querySelector(".referencia-ayuda");
    if (ayudaRef) ayudaRef.textContent = `Código Generado: ${referencia}`;

    calcularYValidar();
  }

  if (btnGenerarRef) btnGenerarRef.addEventListener("click", generarReferencia);

  // Cargar lista de artículos por API
  function cargarArticulosAPI() {
    fetch("/api/articulos/")
      .then((res) => res.json())
      .then((data) => {
        articulosCache = data;
        poblarSelectArticulos(data);
      })
      .catch(() => {});
  }

  function poblarSelectArticulos(articulos) {
    if (!selectArticulo) return;
    const valActual = selectArticulo.value;

    selectArticulo.innerHTML = '<option value="" disabled selected>-- Selecciona un Producto --</option>';

    articulos.forEach((art) => {
      const option = document.createElement("option");
      option.value = art.id;
      option.textContent = `${art.nombre} (${art.codigo})`;
      option.dataset.unidad = art.unidad_medida || "UN";
      option.dataset.stock = art.stock_actual || 0;
      option.dataset.costo_promedio = art.costo_promedio || 0;
      option.dataset.precio_venta = art.precio_venta || 0;
      option.dataset.imagen = art.imagen || "";
      option.dataset.categoria = art.categoria ? art.categoria.nombre : "Sin categoría";

      if (valActual && String(art.id) === String(valActual)) {
        option.selected = true;
      }

      selectArticulo.appendChild(option);
    });

    actualizarMetricasContables();
  }

  // Filtro de Búsqueda Rápida en Vivo
  if (inputFiltroArticulo) {
    inputFiltroArticulo.addEventListener("input", function () {
      const q = inputFiltroArticulo.value.trim().toLowerCase();
      if (!articulosCache || articulosCache.length === 0) return;

      const filtrados = articulosCache.filter((art) => {
        const nom = (art.nombre || "").toLowerCase();
        const cod = (art.codigo || "").toLowerCase();
        const bar = (art.codigo_barras || "").toLowerCase();
        return nom.includes(q) || cod.includes(q) || bar.includes(q);
      });

      poblarSelectArticulos(filtrados);
    });
  }

  // Obtener datos completos del artículo seleccionado
  function obtenerArticuloSeleccionado() {
    if (!selectArticulo || !selectArticulo.value) return null;
    const selectedVal = String(selectArticulo.value);

    let artObj = articulosCache.find((a) => String(a.id) === selectedVal);
    if (artObj) return artObj;

    const opt = selectArticulo.options[selectArticulo.selectedIndex];
    if (!opt || opt.disabled) return null;

    return {
      id: opt.value,
      nombre: opt.textContent,
      unidad_medida: opt.dataset.unidad || "UN",
      stock_actual: parseFloat(opt.dataset.stock) || 0,
      costo_promedio: parseFloat(opt.dataset.costo_promedio) || 0,
      precio_venta: parseFloat(opt.dataset.precio_venta) || 0,
      imagen: opt.dataset.imagen || "",
      categoria: { nombre: opt.dataset.categoria || "General" }
    };
  }

  // Cálculos Financieros y Contables en Tiempo Real
  function actualizarMetricasContables() {
    const artData = obtenerArticuloSeleccionado();

    const cantidad = parseFloat(inputCantidad ? inputCantidad.value : 0) || 0;
    const costoUnitarioCompra = parseFloat(inputCostoUnitario ? inputCostoUnitario.value : 0) || 0;

    if (!artData) {
      if (resumenArticuloText) resumenArticuloText.textContent = "No seleccionado";
      if (categoriaBadge) categoriaBadge.textContent = "Selecciona un producto";
      if (stockActualText) stockActualText.textContent = "0.00";
      if (stockFuturoText) stockFuturoText.textContent = "0.00";
      if (precioReferenciaText) precioReferenciaText.textContent = "COP 0.00";
      if (nuevoCppText) nuevoCppText.textContent = "COP 0.00";
      if (totalCompraText) totalCompraText.textContent = "COP 0.00";
      if (imgArticulo) imgArticulo.classList.add("hidden");
      if (imgPlaceholder) imgPlaceholder.classList.remove("hidden");
      if (variacionPrecioDiv) variacionPrecioDiv.innerHTML = "";
      if (comparacionVentaDiv) comparacionVentaDiv.innerHTML = "";
      return;
    }

    // Actualizar Resumen Visual del Producto
    if (resumenArticuloText) resumenArticuloText.textContent = artData.nombre;
    if (categoriaBadge) categoriaBadge.textContent = artData.categoria ? artData.categoria.nombre : "General";

    const unidad = artData.unidad_medida || "UN";
    document.querySelectorAll(".unidad-medida").forEach(el => el.textContent = unidad);

    let imgUrl = artData.imagen || "";
    if (imgUrl && !imgUrl.startsWith("http://") && !imgUrl.startsWith("https://") && !imgUrl.startsWith("/")) {
      imgUrl = "/media/" + imgUrl;
    }

    if (imgUrl && imgArticulo) {
      imgArticulo.src = imgUrl;
      imgArticulo.classList.remove("hidden");
      if (imgPlaceholder) imgPlaceholder.classList.add("hidden");
    } else {
      if (imgArticulo) imgArticulo.classList.add("hidden");
      if (imgPlaceholder) imgPlaceholder.classList.remove("hidden");
    }

    // Cálculo de Stock Futuro Proyectado
    const stockActual = parseFloat(artData.stock_actual) || 0;
    const stockFuturo = stockActual + cantidad;
    if (stockActualText) stockActualText.textContent = stockActual.toFixed(2);
    if (stockFuturoText) stockFuturoText.textContent = stockFuturo.toFixed(2);

    // Total de la Inversión de Compra
    const totalInversion = cantidad * costoUnitarioCompra;
    if (totalCompraText) totalCompraText.textContent = `COP ${totalInversion.toLocaleString("es-CO", { minimumFractionDigits: 2 })}`;

    // Cálculo de Costo Promedio Ponderado (CPP) Contable
    const cppActual = parseFloat(artData.costo_promedio) || 0;
    let nuevoCPP = cppActual;

    if (stockFuturo > 0 && cantidad > 0 && costoUnitarioCompra > 0) {
      nuevoCPP = ((stockActual * cppActual) + (cantidad * costoUnitarioCompra)) / stockFuturo;
    }

    if (precioReferenciaText) precioReferenciaText.textContent = `COP ${cppActual.toLocaleString("es-CO", { minimumFractionDigits: 2 })}`;
    if (nuevoCppText) nuevoCppText.textContent = `COP ${nuevoCPP.toLocaleString("es-CO", { minimumFractionDigits: 2 })}`;

    // Variación del Costo de Compra vs CPP Anterior
    if (costoUnitarioCompra > 0 && cppActual > 0) {
      const diffPorcentaje = ((costoUnitarioCompra - cppActual) / cppActual) * 100;
      if (diffPorcentaje < 0) {
        variacionPrecioDiv.innerHTML = `
          <span class="inline-flex items-center gap-1 text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md text-[11px] font-bold">
            <i class="bi bi-arrow-down-right-circle-fill"></i>
            Ahorro en Compra: ${Math.abs(diffPorcentaje).toFixed(1)}% menor al CPP anterior
          </span>
        `;
      } else if (diffPorcentaje > 0) {
        variacionPrecioDiv.innerHTML = `
          <span class="inline-flex items-center gap-1 text-amber-800 bg-amber-100 px-2 py-0.5 rounded-md text-[11px] font-bold">
            <i class="bi bi-arrow-up-right-circle-fill"></i>
            Incremento: +${diffPorcentaje.toFixed(1)}% mayor al CPP anterior
          </span>
        `;
      } else {
        variacionPrecioDiv.innerHTML = `<span class="text-slate-500 text-[11px]">Mismo costo de compra actual</span>`;
      }
    } else {
      if (variacionPrecioDiv) variacionPrecioDiv.innerHTML = "";
    }

    // Simulación del Margen Bruto Proyectado
    const pvpVenta = parseFloat(artData.precio_venta) || 0;
    if (pvpVenta > 0 && nuevoCPP > 0) {
      const margenProyectado = ((pvpVenta - nuevoCPP) / pvpVenta) * 100;
      const claseMargen = margenProyectado >= 15 ? 'text-emerald-700 bg-emerald-100' : (margenProyectado > 0 ? 'text-amber-800 bg-amber-100' : 'text-rose-800 bg-rose-100');
      
      if (comparacionVentaDiv) {
        comparacionVentaDiv.innerHTML = `
          <div class="flex items-center justify-between mt-1">
            <span class="text-[11px] text-slate-500">PVP Venta: <strong>COP ${pvpVenta.toLocaleString("es-CO")}</strong></span>
            <span class="px-2 py-0.5 rounded-md text-[11px] font-bold ${claseMargen}">
              Margen Bruto Proyectado: ${margenProyectado.toFixed(1)}%
            </span>
          </div>
        `;
      }
    } else {
      if (comparacionVentaDiv) comparacionVentaDiv.innerHTML = "";
    }
  }

  // Validación General del Formulario
  function calcularYValidar() {
    actualizarMetricasContables();

    const tieneArticulo = selectArticulo && selectArticulo.value && selectArticulo.value !== "";
    const cantidadValida = inputCantidad && parseFloat(inputCantidad.value) > 0;
    const costoValido = inputCostoUnitario && parseFloat(inputCostoUnitario.value) > 0;
    const refValida = inputReferencia && inputReferencia.value.trim().length >= 3;

    const formValido = tieneArticulo && cantidadValida && costoValido && refValida;

    if (estadoFormulario) {
      if (formValido) {
        estadoFormulario.className = "text-[11px] font-bold text-emerald-900 bg-emerald-300 px-2.5 py-0.5 rounded-full";
        estadoFormulario.textContent = "Formulario Listo";
      } else {
        estadoFormulario.className = "text-[11px] font-bold text-amber-900 bg-amber-300 px-2.5 py-0.5 rounded-full";
        estadoFormulario.textContent = "Incompleto";
      }
    }

    if (submitBtn) {
      submitBtn.disabled = !formValido;
    }
  }

  // Event Listeners
  if (selectArticulo) {
    selectArticulo.addEventListener("change", calcularYValidar);
    selectArticulo.addEventListener("input", calcularYValidar);
  }
  if (inputCantidad) {
    inputCantidad.addEventListener("input", calcularYValidar);
    inputCantidad.addEventListener("change", calcularYValidar);
  }
  if (inputCostoUnitario) {
    inputCostoUnitario.addEventListener("input", calcularYValidar);
    inputCostoUnitario.addEventListener("change", calcularYValidar);
  }
  if (inputReferencia) inputReferencia.addEventListener("input", calcularYValidar);

  // Inicialización
  cargarArticulosAPI();
  if (inputReferencia && (!inputReferencia.value || inputReferencia.value.trim() === "")) {
    generarReferencia();
  }
});
