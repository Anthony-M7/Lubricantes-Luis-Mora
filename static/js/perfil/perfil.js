document.addEventListener('DOMContentLoaded', function() {
    // Elementos principales
    const editBtn = document.getElementById('edit-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveBtn = document.getElementById('save-btn');
    const editButtons = document.getElementById('edit-buttons');
    const profileForm = document.getElementById('profile-form');
    
    // Elementos de foto de perfil (verificamos si existen)
    const changePhotoBtn = document.getElementById('change-photo-btn');
    const fotoPerfilInput = document.getElementById('id_foto_perfil');
    const profilePicture = document.getElementById('profile-picture');
    
    // Verificación de elementos antes de agregar event listeners
    if (!editBtn || !cancelBtn || !saveBtn || !editButtons || !profileForm) {
        console.error('Error: No se encontraron elementos esenciales del formulario');
        return;
    }
    
    // Guardar los valores originales para poder cancelar
    let originalValues = {};
    
    editBtn.addEventListener('click', function() {
        // Obtener y guardar los valores originales del formulario
        originalValues = {};
        document.querySelectorAll('.edit-mode input, .edit-mode select').forEach(field => {
            originalValues[field.name] = field.type === 'checkbox' ? field.checked : field.value;
        });
        
        // Cambiar a modo edición
        toggleEditMode(true);
    });
    
    cancelBtn.addEventListener('click', function() {
        // Restaurar los valores originales
        Object.keys(originalValues).forEach(name => {
            const field = document.querySelector(`[name="${name}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = originalValues[name];
                } else {
                    field.value = originalValues[name];
                }
            }
        });
        
        // Volver a modo visualización
        toggleEditMode(false);
    });
    
    saveBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Validación básica
        const username = document.getElementById('id_username');
        const email = document.getElementById('id_email');
        
        if (!username || !username.value.trim()) {
            alert('El nombre de usuario es obligatorio');
            return;
        }
        
        if (!email || !email.value.trim()) {
            alert('El correo electrónico es obligatorio');
            return;
        }
        
        // Enviar el formulario
        profileForm.submit();
    });
    
    function toggleEditMode(edit) {
        // Mostrar/ocultar modos
        const viewMode = document.querySelector('.view-mode');
        const editMode = document.querySelector('.edit-mode');
        
        if (viewMode) viewMode.style.display = edit ? 'none' : 'block';
        if (editMode) editMode.style.display = edit ? 'flex' : 'none';
        
        // Mostrar/ocultar botones
        editBtn.style.display = edit ? 'none' : 'block';
        editButtons.style.display = edit ? 'flex' : 'none';
        
        // Mostrar botón de cambiar foto solo si existe
        if (changePhotoBtn) {
            changePhotoBtn.style.display = edit ? 'block' : 'none';
        }
    }
    
    // Manejar el cambio de foto de perfil solo si los elementos existen
    if (changePhotoBtn && fotoPerfilInput) {
        changePhotoBtn.addEventListener('click', function() {
            fotoPerfilInput.click();
        });
        
        fotoPerfilInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && profilePicture) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    profilePicture.src = event.target.result;
                };
                reader.readAsDataURL(file);
                changePhotoBtn.textContent = file.name;
            }
        });
    }
});