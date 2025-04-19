const loader = document.getElementById('global-loader');

function showLoader() {
    loader.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function hideLoader() {
    loader.style.display = 'none';
    document.body.style.overflow = '';
}

document.getElementById('descargar-recibo-btn').addEventListener('click', function (e) {
    e.preventDefault();

    let id = this.getAttribute('data-idVenta');
    let codigo = this.getAttribute('data-codigoVenta');

    const url = `/venta/${id}/descargar_recibo/`;

    showLoader();
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Error al descargar');
            return response.blob();
        })
        .then(blob => {
            const a = document.createElement('a');
            const urlBlob = window.URL.createObjectURL(blob);
            a.href = urlBlob;
            a.download = `recibo_venta_${codigo}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(urlBlob);
        })
        .catch(err => {
            console.error(err);
            alert('Error al generar el recibo');
        })
        .finally(() => {
            hideLoader();
        });
});
