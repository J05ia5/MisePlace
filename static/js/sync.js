/**
 * Sincronización en tiempo real para MisePlace
 * Comprueba periódicamente cambios en la base de datos para alertar a los usuarios.
 */
(() => {
    let initialVersion = null;
    let alertShown = false;

    async function checkStateChanges() {
        if (document.hidden || alertShown) return;
        try {
            const res = await fetch('/reportes/api/estado-sistema/', {
                cache: 'no-store',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!res.ok) return;

            const data = await res.json();
            if (!initialVersion) {
                initialVersion = data.version;
                return;
            }

            if (data.version !== initialVersion) {
                alertShown = true;
                const banner = document.createElement('div');
                banner.className = 'sync-alert-banner';
                banner.setAttribute('role', 'status');
                banner.innerHTML = `
                    <span>Hay información nueva actualizada por otro usuario.</span>
                    <button type="button" class="btn btn-secondary btn-sm" id="btnRecargarSistema">Actualizar ahora</button>
                `;
                document.body.appendChild(banner);
                document.getElementById('btnRecargarSistema')?.addEventListener('click', () => {
                    window.location.reload();
                });
            }
        } catch (_) {
            // Silencioso ante pérdidas temporales de conexión
        }
    }

    // Inicializar sondeo cada 5 segundos
    checkStateChanges();
    window.setInterval(checkStateChanges, 5000);
})();
