document.addEventListener("DOMContentLoaded", function () {
  const filtroBtns = document.querySelectorAll("#filtro-transacciones button");
  const filasTabla = document.querySelectorAll("#tabla-transacciones tbody tr");

  filtroBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      // Remover clase active de todos los botones
      filtroBtns.forEach((b) => b.classList.remove("active", "btn-primary"));
      filtroBtns.forEach((b) => b.classList.add("btn-outline-secondary"));

      // Añadir clase active al botón clickeado
      this.classList.add("active", "btn-primary");
      this.classList.remove("btn-outline-secondary");

      const filtro = this.getAttribute("data-filtro");

      // Filtrar las filas
      filasTabla.forEach((fila) => {
        const tipoFila = fila.getAttribute("data-tipo");

        if (filtro === "todas" || tipoFila === filtro) {
          fila.style.display = "";
        } else {
          fila.style.display = "none";
        }
      });
    });
  });
});

// Control de notificaciones
document.addEventListener('DOMContentLoaded', function() {
  // Cerrar notificaciones
  const closeButtons = document.querySelectorAll('.btn-close');
  closeButtons.forEach(button => {
      button.addEventListener('click', function() {
          this.closest('.toast').classList.remove('show');
      });
  });
  
  // Cerrar notificaciones automáticamente después de 5 segundos
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach(toast => {
      setTimeout(() => {
          toast.classList.remove('show');
      }, 5000);
  });
  
  // Filtro de transacciones (existente)
  const filtroBtns = document.querySelectorAll("#filtro-transacciones button");
  const filasTabla = document.querySelectorAll("#tabla-transacciones tbody tr");

  filtroBtns.forEach((btn) => {
      btn.addEventListener("click", function() {
          // Remover clase active de todos los botones
          filtroBtns.forEach((b) => b.classList.remove("active", "btn-primary"));
          filtroBtns.forEach((b) => b.classList.add("btn-outline-secondary"));

          // Añadir clase active al botón clickeado
          this.classList.add("active", "btn-primary");
          this.classList.remove("btn-outline-secondary");

          const filtro = this.getAttribute("data-filtro");

          // Filtrar las filas
          filasTabla.forEach((fila) => {
              const tipoFila = fila.getAttribute("data-tipo");

              if (filtro === "todas" || tipoFila === filtro) {
                  fila.style.display = "";
              } else {
                  fila.style.display = "none";
              }
          });
      });
  });
});