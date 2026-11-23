import './styles/base.css'

const root = document.getElementById('app')
if (root === null) {
  throw new Error('No existe el contenedor principal de NeuroVision')
}

// Punto de entrada provisional; las pantallas definitivas pertenecen a Johan.
root.innerHTML = `
  <main class="shell">
    <p class="eyebrow">Prototipo académico · Estructura inicial</p>
    <h1>NeuroVision</h1>
    <p>La arquitectura y los contratos están preparados para comenzar el desarrollo.</p>
    <p class="status">Visor de resonancias y segmentación: pendientes de implementación.</p>
  </main>
`
