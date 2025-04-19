// Función para mostrar el modal de confirmación

document.addEventListener("DOMContentLoaded", function() {
  const confirmDeleteModal = new bootstrap.Modal('#confirmDeleteModal');
  let currentVentaId = null;
  
  // Configurar botones de eliminar
  document.querySelectorAll('.delete-venta').forEach(btn => {
    btn.addEventListener('click', function() {
      currentVentaId = this.getAttribute('data-id');
    });
  });
  
  // Configurar botón de confirmación
  document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
    if (!currentVentaId) return;
    
    // Mostrar indicador de carga
    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Eliminando...';
    this.disabled = true;
    
    // Realizar la petición DELETE
    fetch(`/ventas/${currentVentaId}/eliminar/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      if (!response.ok) throw new Error('Error en la respuesta del servidor');
      return response.json();
    })
    .then(data => {
      if (data.success) {
        // Mostrar mensaje de éxito y recargar o actualizar la tabla
        showAlert('Venta eliminada correctamente', 'success');
        // Opción 1: Recargar la página
        window.location.reload();
        // Opción 2: Eliminar la fila de la tabla sin recargar
        // document.querySelector(`tr[data-venta-id="${currentVentaId}"]`).remove();
      } else {
        throw new Error(data.error || 'Error al eliminar la venta');
      }
    })
    .catch(error => {
      showAlert(error.message, 'danger');
    })
    .finally(() => {
      confirmDeleteModal.hide();
      this.innerHTML = 'Eliminar';
      this.disabled = false;
    });
  });
  
  // Función para obtener el token CSRF
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
  
  // Función para mostrar alertas
  function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container') || document.body;
    container.prepend(alertDiv);
    
    setTimeout(() => {
      alertDiv.classList.remove('show');
      setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
  }
});