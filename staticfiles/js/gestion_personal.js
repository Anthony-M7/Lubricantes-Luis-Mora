document.addEventListener("DOMContentLoaded", function () {
  const personalModal = document.getElementById("personalModal");
  const personalForm = document.getElementById("personalForm");
  const confirmModal = document.getElementById("confirmModal");
  let personalIdToDelete = null;

  // Configurar modal para agregar/editar
  // En el evento show.bs.modal
  personalModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    const action = button.getAttribute("data-action");
    const modalTitle = personalModal.querySelector(".modal-title");
    const form = personalModal.querySelector("form");

    if (action === "add") {
      modalTitle.textContent = "Agregar Nuevo Personal";
      form.reset();
      form.querySelector("#personal_id").value = "";
      form.querySelector("#username").disabled = false;
    } else {
      modalTitle.textContent = "Editar Personal";
      const personalId = button.getAttribute("data-id");
      form.querySelector("#personal_id").value = personalId;
      form.querySelector("#username").disabled = true;

      // Cargar datos existentes
      fetch(`/get_personal_data/${personalId}/`)
        .then((response) => response.json())
        .then((data) => {
          for (const field in data) {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
              if (input.type === "file") continue;
              input.value = data[field] || "";
            }
          }
        });
    }
  });

  personalForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const personalId = formData.get("id");
    const url = personalId ? "/editar_personal/" : "/crear_personal/";

    // Si es edición, agregar el username manualmente (ya que el campo está disabled)
    if (personalId) {
      const usernameInput = document.getElementById("username");
      formData.append("username", usernameInput.value);
    }

    // Mostrar indicador de carga
    const submitBtn = personalForm.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';

    try {
      // Validación básica en el cliente
      const username = formData.get("username");
      if (!username || username.trim() === "") {
        throw new Error("El nombre de usuario es requerido");
      }

      const response = await fetch(url, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });

      const data = await response.json();

      if (!response.ok) {
        // Manejo mejorado de errores del servidor
        let errorMessage = "Error en el servidor:\n";
        if (data.errors) {
          for (const field in data.errors) {
            errorMessage += `• ${field}: ${data.errors[field].join(", ")}\n`;
          }
        } else if (data.error) {
          errorMessage += data.error;
        } else {
          errorMessage += "Error desconocido";
        }
        throw new Error(errorMessage);
      }

      if (data.success) {
        // Cerrar modal y actualizar interfaz
        const modal = bootstrap.Modal.getInstance(personalModal);
        modal.hide();

        // Actualizar la tabla sin recargar
        if (personalId) {
          updatePersonalRow(data.personal);
        } else {
          addNewPersonalRow(data.personal);
        }

        // Mostrar notificación de éxito
        showAlert("success", "Operación realizada con éxito");
      } else {
        throw new Error("La operación no fue exitosa");
      }
    } catch (error) {
      console.error("Error:", error);
      showAlert("danger", error.message);
    } finally {
      // Restaurar botón
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnText;
    }
  });

  // Función para mostrar alertas
  function showAlert(type, message) {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = "alert";
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Insertar al inicio del contenedor principal
    const container = document.querySelector(".container");
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
      alertDiv.remove();
    }, 5000);
  }

  // Función para actualizar fila existente
  function updatePersonalRow(personalData) {
    const row = document.querySelector(`tr[data-id="${personalData.id}"]`);
    if (!row) return;

    // Actualizar cada campo
    row.querySelector("td:nth-child(2)").innerHTML =
        personalData.foto
          ? `<div class="d-flex align-items-center" bis_skin_checked="1">
                <img src="${personalData.foto}" class="rounded-circle me-2" width="40" height="40" alt="Foto de ${personalData.nombre_completo}">
                <div bis_skin_checked="1">
                    <strong>${personalData.nombre_completo}</strong><br>
                    <small class="text-muted">@${personalData.username}</small>
                </div>
            </div>`
        : `<div class="d-flex align-items-center" bis_skin_checked="1">
                <div class="rounded-circle bg-secondary me-2 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"> <span class="text-white">${personalData.nombre_completo.charAt(0).toUpperCase()}</span></div>
                <div bis_skin_checked="1">
                    <strong>${personalData.nombre_completo}</strong><br>
                    <small class="text-muted">@${personalData.username}</small>
                </div>
            </div>
          `

    row.querySelector("td:nth-child(3)").innerHTML = `<span class="badge bg-${
        personalData.rol === "admin" ? "primary" : "info"
      }">${personalData.rol}</span>`;
    row.querySelector("td:nth-child(4) div:nth-child(1)").textContent =
      personalData.email;
    row.querySelector("td:nth-child(4) div:nth-child(2)").textContent =
      personalData.telefono || "-";
  }

  // Función para añadir nueva fila
  function addNewPersonalRow(personalData) {
    const tbody = document.querySelector("#personalTable tbody");
    const newRow = document.createElement("tr");
    newRow.setAttribute("data-id", personalData.id);

    newRow.innerHTML = `
      <td>${tbody.children.length + 1}</td>
      <td>
        <div class="d-flex align-items-center">
        ${
          personalData.foto
            ? `<img src="${personalData.foto}" alt="Foto" class="rounded-circle me-2" style="width: 40px; height: 40px;">`
            : '<div class="rounded-circle bg-secondary me-2 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"> <span class="text-white">${personalData.nombre_completo.charAt(0).toUpperCase()}</span></div>'
        }
          <div>
            <strong>${personalData.nombre_completo}</strong><br>
            <small class="text-muted">@${personalData.username}</small>
          </div>
        </div>
      </td>
      <td><span class="badge bg-${
        personalData.rol === "admin" ? "primary" : "info"
      }">${personalData.rol}</span></td>
      <td>
        <div><i class="bi bi-envelope"></i> ${personalData.email}</div>
        <div><i class="bi bi-telephone"></i> ${
          personalData.telefono || "-"
        }</div>
      </td>
      <td>
        <div class="btn-group btn-group-sm">
          <button class="btn btn-outline-primary btn-editar" data-id="${
            personalData.id
          }" data-bs-toggle="modal" data-bs-target="#personalModal">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-outline-danger btn-eliminar" data-id="${
            personalData.id
          }" data-bs-toggle="modal" data-bs-target="#confirmModal">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </td>
    `;

    tbody.appendChild(newRow);
  }

  // Configurar modal de confirmación para eliminar
  confirmModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    personalIdToDelete = button.getAttribute("data-id");
  });

  // Manejar eliminación
  document
    .getElementById("confirmDelete")
    .addEventListener("click", function () {
      if (!personalIdToDelete) return;

      fetch(`/eliminar_personal/${personalIdToDelete}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            document
              .querySelector(`tr[data-id="${personalIdToDelete}"]`)
              .remove();
            bootstrap.Modal.getInstance(confirmModal).hide();
          } else {
            alert(data.error || "Error al eliminar");
          }
        });
    });

  // Función para obtener cookie CSRF
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
