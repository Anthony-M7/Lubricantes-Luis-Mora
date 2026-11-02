document.addEventListener('DOMContentLoaded', function () {
    // Toggle entre Vistas (Cuadrícula vs Lista) con TailwindCSS y LocalStorage
    const gridViewBtn = document.getElementById('gridViewBtn');
    const listViewBtn = document.getElementById('listViewBtn');
    const gridView = document.getElementById('gridView');
    const listView = document.getElementById('listView');

    function activarVistaCuadricula() {
        if (!gridView || !listView) return;
        gridView.classList.remove('hidden');
        listView.classList.add('hidden');

        // Estilos Botones Tailwind
        gridViewBtn.className = 'px-3 py-1.5 rounded-lg text-sm font-bold text-brand-dark bg-white shadow-sm transition border border-slate-200/60';
        listViewBtn.className = 'px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-900 transition bg-transparent';

        localStorage.setItem('inventoryViewMode', 'grid');
    }

    function activarVistaLista() {
        if (!gridView || !listView) return;
        listView.classList.remove('hidden');
        gridView.classList.add('hidden');

        // Estilos Botones Tailwind
        listViewBtn.className = 'px-3 py-1.5 rounded-lg text-sm font-bold text-brand-dark bg-white shadow-sm transition border border-slate-200/60';
        gridViewBtn.className = 'px-3 py-1.5 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-900 transition bg-transparent';

        localStorage.setItem('inventoryViewMode', 'list');
    }

    if (gridViewBtn) gridViewBtn.addEventListener('click', activarVistaCuadricula);
    if (listViewBtn) listViewBtn.addEventListener('click', activarVistaLista);

    // Cargar preferencia guardada
    const savedMode = localStorage.getItem('inventoryViewMode');
    if (savedMode === 'list') {
        activarVistaLista();
    } else {
        activarVistaCuadricula();
    }

    // Submit de filtros y búsqueda
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const statusFilter = document.getElementById('statusFilter');
    const clearSearch = document.getElementById('clearSearch');

    function updateFilters() {
        const params = new URLSearchParams(window.location.search);
        if (searchInput && searchInput.value) {
            params.set('q', searchInput.value);
        } else {
            params.delete('q');
        }

        if (categoryFilter && categoryFilter.value) {
            params.set('categoria', categoryFilter.value);
        } else {
            params.delete('categoria');
        }

        if (statusFilter && statusFilter.value) {
            params.set('estado', statusFilter.value);
        } else {
            params.delete('estado');
        }

        window.location.search = params.toString();
    }

    if (searchInput) {
        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') updateFilters();
        });
    }

    if (categoryFilter) categoryFilter.addEventListener('change', updateFilters);
    if (statusFilter) statusFilter.addEventListener('change', updateFilters);

    if (clearSearch) {
        clearSearch.addEventListener('click', function () {
            window.location.href = window.location.pathname;
        });
    }
});
