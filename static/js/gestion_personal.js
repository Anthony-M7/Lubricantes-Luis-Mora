document.addEventListener("DOMContentLoaded", function () {
  const personalModal = document.getElementById("personalModal");
  const personalForm = document.getElementById("personalForm");
  const confirmModal = document.getElementById("confirmModal");
  let personalIdToDelete = null;

  // Global functions to open/close modals for HTML onclick
  window.openPersonalModal = function(action, id = null) {
    const modalTitle = document.getElementById("modalTitleText");
    const form = document.getElementById("personalForm");

    if (action === "add") {
      modalTitle.textContent = "Agregar Nuevo Personal";
      form.reset();
      form.querySelector("#personal_id").value = "";
      form.querySelector("#username").disabled = false;
    } else if (action === "edit" && id) {
      modalTitle.textContent = "Editar Personal";
      form.querySelector("#personal_id").value = id;
      form.querySelector("#username").disabled = true;

      // Fetch existing data
      fetch(`/get_personal_data/${id}/`)
        .then((response) => response.json())
        .then((data) => {
          for (const field in data) {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
              if (input.type === "file") continue;
              input.value = data[field] || "";
            }
          }
        })
        .catch(err => {
          console.error("Error fetching data", err);
          showAlert("error", "No se pudo cargar la información del usuario.");
        });
    }
    
    // Show modal
    personalModal.classList.remove("hidden");
  };

  window.openConfirmModal = function(id) {
    personalIdToDelete = id;
    confirmModal.classList.remove("hidden");
  };

  window.closeModal = function(modalId) {
    document.getElementById(modalId).classList.add("hidden");
    if (modalId === "confirmModal") {
        personalIdToDelete = null;
    }
  };

  // Close modals when clicking outside
  window.addEventListener("click", function (event) {
    if (event.target === personalModal) {
      closeModal("personalModal");
    }
    if (event.target === confirmModal) {
      closeModal("confirmModal");
    }
  });

  // Handle Form Submission
  if (personalForm) {
    personalForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const personalId = formData.get("id");
      const url = personalId ? "/editar_personal/" : "/crear_personal/";

      // If edit, append the disabled username field
      if (personalId) {
        const usernameInput = document.getElementById("username");
        formData.append("username", usernameInput.value);
      }

      // Show loading indicator
      const submitBtn = personalForm.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML =
        '<i class="bi bi-arrow-repeat animate-spin mr-2"></i> Procesando...';

      try {
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
          closeModal("personalModal");

          if (personalId) {
            updatePersonalRow(data.personal);
          } else {
            addNewPersonalRow(data.personal);
          }
          showAlert("success", "Operación realizada con éxito");
        } else {
          throw new Error("La operación no fue exitosa");
        }
      } catch (error) {
        console.error("Error:", error);
        showAlert("error", error.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
      }
    });
  }

  // Handle Delete Confirmation
  const confirmDeleteBtn = document.getElementById("confirmDelete");
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", function () {
      if (!personalIdToDelete) return;
      
      const originalBtnText = this.innerHTML;
      this.disabled = true;
      this.innerHTML = '<i class="bi bi-arrow-repeat animate-spin mr-2"></i> Eliminando...';

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
            const row = document.querySelector(`tr[data-id="${personalIdToDelete}"]`);
            if (row) row.remove();
            closeModal("confirmModal");
            showAlert("success", "Personal eliminado correctamente");
          } else {
            showAlert("error", data.error || "Error al eliminar");
          }
        })
        .catch(err => {
            console.error(err);
            showAlert("error", "Error de conexión al eliminar.");
        })
        .finally(() => {
            this.disabled = false;
            this.innerHTML = originalBtnText;
        });
    });
  }

  // Function to show custom alert overlay like base.html
  function showAlert(type, message) {
    const isError = type === 'error' || type === 'danger';
    
    // Create the modal container
    const alertDiv = document.createElement("div");
    alertDiv.className = "fixed inset-0 z-[100] overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 alert-modal transition-opacity";
    
    const iconClass = isError ? "bi-exclamation-triangle-fill" : "bi-check-circle-fill";
    const bgIcon = isError ? "bg-rose-100 text-rose-600 border-rose-200" : "bg-emerald-100 text-emerald-600 border-emerald-200";
    const titleText = isError ? "¡Error!" : "¡Éxito!";
    const btnBg = isError ? "bg-rose-600 hover:bg-rose-700" : "bg-emerald-600 hover:bg-emerald-700";
    
    alertDiv.innerHTML = `
      <div class="relative w-full max-w-sm bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200 animate-in fade-in zoom-in duration-200">
        <div class="p-6 text-center space-y-4">
          <div class="mx-auto w-16 h-16 rounded-2xl flex items-center justify-center shadow-sm border ${bgIcon}">
            <i class="bi ${iconClass} text-3xl"></i>
          </div>
          <div class="space-y-1">
            <h3 class="text-base font-black text-slate-900">${titleText}</h3>
            <p class="text-xs font-semibold text-slate-600 leading-relaxed" style="white-space: pre-wrap;">${message}</p>
          </div>
          <div class="pt-2">
            <button type="button" class="w-full py-2.5 px-4 rounded-xl text-xs font-extrabold text-white shadow-md transition transform active:scale-95 close-alert-btn ${btnBg}">
              Aceptar
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(alertDiv);
    
    // Add close event
    alertDiv.querySelector('.close-alert-btn').addEventListener('click', () => {
        alertDiv.remove();
    });
    
    // Auto-remove after 5s if it's a success
    if (!isError) {
        setTimeout(() => {
            if (document.body.contains(alertDiv)) {
                alertDiv.remove();
            }
        }, 5000);
    }
  }

  // Update existing row
  function updatePersonalRow(personalData) {
    const row = document.querySelector(`tr[data-id="${personalData.id}"]`);
    if (!row) return;

    let roleBadgeColor = "bg-emerald-100 text-emerald-700";
    let roleIcon = "bi-person-badge";
    if (personalData.rol === "admin") { roleBadgeColor = "bg-purple-100 text-purple-700"; roleIcon = "bi-shield-lock"; }
    else if (personalData.rol === "gerente") { roleBadgeColor = "bg-sky-100 text-sky-700"; roleIcon = "bi-briefcase"; }

    row.querySelector("td:nth-child(2)").innerHTML =
        personalData.foto
          ? `<div class="flex items-center space-x-3">
              <img src="${personalData.foto}" alt="${personalData.nombre_completo}" class="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm" />
              <div>
                <div class="font-bold text-slate-900">${personalData.nombre_completo}</div>
                <div class="text-xs text-slate-500 font-medium">@${personalData.username}</div>
              </div>
            </div>`
          : `<div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-full bg-gradient-to-br from-brand-primary to-brand-dark flex items-center justify-center text-white font-bold text-sm shadow-sm border-2 border-white">
                ${personalData.nombre_completo.charAt(0).toUpperCase()}
              </div>
              <div>
                <div class="font-bold text-slate-900">${personalData.nombre_completo}</div>
                <div class="text-xs text-slate-500 font-medium">@${personalData.username}</div>
              </div>
            </div>`;

    row.querySelector("td:nth-child(3)").innerHTML = `
        <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${roleBadgeColor}">
            <i class="bi ${roleIcon} mr-1"></i> ${personalData.rol.charAt(0).toUpperCase() + personalData.rol.slice(1)}
        </span>
    `;
    
    row.querySelector("td:nth-child(4)").innerHTML = `
        <div class="flex items-center text-xs text-slate-600"><i class="bi bi-envelope text-slate-400 mr-2"></i> ${personalData.email}</div>
        <div class="flex items-center text-xs text-slate-600"><i class="bi bi-telephone text-slate-400 mr-2"></i> ${personalData.telefono || "No registrado"}</div>
    `;
  }

  // Add new row
  function addNewPersonalRow(personalData) {
    const tbody = document.querySelector("#personalTable tbody");
    const emptyRow = tbody.querySelector("td[colspan='5']")?.parentElement;
    if (emptyRow) emptyRow.remove();

    const newRow = document.createElement("tr");
    newRow.className = "hover:bg-slate-50/60 transition group";
    newRow.setAttribute("data-id", personalData.id);

    let roleBadgeColor = "bg-emerald-100 text-emerald-700";
    let roleIcon = "bi-person-badge";
    if (personalData.rol === "admin") { roleBadgeColor = "bg-purple-100 text-purple-700"; roleIcon = "bi-shield-lock"; }
    else if (personalData.rol === "gerente") { roleBadgeColor = "bg-sky-100 text-sky-700"; roleIcon = "bi-briefcase"; }

    newRow.innerHTML = `
      <td class="px-6 py-4 font-medium text-slate-500">${tbody.children.length + 1}</td>
      <td class="px-6 py-4">
        ${
          personalData.foto
            ? `<div class="flex items-center space-x-3">
                <img src="${personalData.foto}" alt="${personalData.nombre_completo}" class="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm" />
                <div>
                  <div class="font-bold text-slate-900">${personalData.nombre_completo}</div>
                  <div class="text-xs text-slate-500 font-medium">@${personalData.username}</div>
                </div>
              </div>`
            : `<div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-brand-primary to-brand-dark flex items-center justify-center text-white font-bold text-sm shadow-sm border-2 border-white">
                  ${personalData.nombre_completo.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div class="font-bold text-slate-900">${personalData.nombre_completo}</div>
                  <div class="text-xs text-slate-500 font-medium">@${personalData.username}</div>
                </div>
              </div>`
        }
      </td>
      <td class="px-6 py-4">
        <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${roleBadgeColor}">
            <i class="bi ${roleIcon} mr-1"></i> ${personalData.rol.charAt(0).toUpperCase() + personalData.rol.slice(1)}
        </span>
      </td>
      <td class="px-6 py-4 space-y-1">
        <div class="flex items-center text-xs text-slate-600"><i class="bi bi-envelope text-slate-400 mr-2"></i> ${personalData.email}</div>
        <div class="flex items-center text-xs text-slate-600"><i class="bi bi-telephone text-slate-400 mr-2"></i> ${personalData.telefono || "No registrado"}</div>
      </td>
      <td class="px-6 py-4 text-right">
        <div class="flex items-center justify-end space-x-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
          <a href="/gestion_permisos_user/${personalData.id}/" class="p-2 text-amber-600 hover:bg-amber-50 rounded-lg transition" title="Permisos">
            <i class="bi bi-key-fill text-lg"></i>
          </a>
          <button class="btn-editar p-2 text-brand-primary hover:bg-brand-50 rounded-lg transition" onclick="openPersonalModal('edit', '${personalData.id}')" title="Editar">
            <i class="bi bi-pencil-square text-lg"></i>
          </button>
          <button class="btn-eliminar p-2 text-rose-600 hover:bg-rose-50 rounded-lg transition" onclick="openConfirmModal('${personalData.id}')" title="Eliminar">
            <i class="bi bi-trash-fill text-lg"></i>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(newRow);
  }

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
