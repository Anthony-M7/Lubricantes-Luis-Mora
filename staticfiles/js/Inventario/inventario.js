document.addEventListener('DOMContentLoaded', function () {
    // Toggle entre vistas
    const gridViewBtn = document.getElementById('gridViewBtn');
    const listViewBtn = document.getElementById('listViewBtn');
    const gridView = document.getElementById('gridView');
    const listView = document.getElementById('listView');

    gridViewBtn.addEventListener('click', function () {
        gridView.classList.remove('d-none');
        listView.classList.add('d-none');
        gridViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
    });

    listViewBtn.addEventListener('click', function () {
        listView.classList.remove('d-none');
        gridView.classList.add('d-none');
        listViewBtn.classList.add('active');
        gridViewBtn.classList.remove('active');
    });

    // Submit de filtros y búsqueda
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const statusFilter = document.getElementById('statusFilter');
    const clearSearch = document.getElementById('clearSearch');

    function updateFilters() {
        const params = new URLSearchParams(window.location.search);
        params.set('q', searchInput.value);
        params.set('categoria', categoryFilter.value);
        params.set('estado', statusFilter.value);
        window.location.search = params.toString();
    }

    searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') updateFilters();
    });

    categoryFilter.addEventListener('change', updateFilters);
    statusFilter.addEventListener('change', updateFilters);

    clearSearch.addEventListener('click', function () {
        window.location.search = '';
    });
});
