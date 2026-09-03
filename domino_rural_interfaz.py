"""Interfaz web de Dominó Rural con diseño S.I.G.E.A."""

CSS = """
:root {
  --verde-primario: #059669;
  --verde-oscuro: #065f46;
  --verde-claro: #d1fae5;
  --fondo-gris: #f3f4f6;
  --texto-principal: #1f2937;
  --texto-secundario: #4b5563;
  --blanco: #ffffff;
  --borde: #e5e7eb;
  --rojo-alerta: #dc2626;
  --sombra: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background-color: var(--fondo-gris);
  color: var(--texto-principal);
  font-family: 'Inter', sans-serif;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

header {
  background: linear-gradient(135deg, var(--verde-oscuro) 0%, var(--verde-primario) 100%);
  color: var(--blanco);
  padding: 2.5rem 1.5rem;
  text-align: center;
  border-bottom: 5px solid #10b981;
}

.header-titulo { display: flex; align-items: center; justify-content: center; gap: 12px; }
header h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
header span {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.4rem 0.9rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.container {
  max-width: 1100px;
  margin: 2.5rem auto 1.5rem auto;
  padding: 0 1.5rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.card {
  background-color: var(--blanco);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: var(--sombra);
  border: 1px solid var(--borde);
  display: flex;
  flex-direction: column;
}

.card.full-width { grid-column: 1 / -1; }

.card h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--texto-principal);
  margin-bottom: 1.25rem;
  border-bottom: 2px solid var(--fondo-gris);
  padding-bottom: 0.75rem;
}

#leyenda {
  display: flex; gap: 20px; margin-bottom: 16px; font-size: 0.85rem; color: var(--texto-secundario);
}
.leyenda-item { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.punto { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.punto.verde { background: #2ecc71; }
.punto.rojo { background: #e74c3c; }
.punto.gris { background: #9ca3af; }

label { display: block; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.5rem; color: var(--texto-secundario); }

select, button {
  width: 100%; padding: 0.9rem; border-radius: 8px; border: 1px solid var(--borde);
  font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease;
  margin-bottom: 10px;
}

select { background: #f9fafb; color: var(--texto-principal); }

.btn-analizar { background-color: var(--verde-primario); color: white; border: none; }
.btn-analizar:hover { background-color: var(--verde-oscuro); }
.btn-reset { background-color: #9ca3af; color: white; border: none; }
.btn-reset:hover { background-color: #6b7280; }
.btn-success { background-color: #2563eb; color: white; border: none; }
.btn-success:hover { background-color: #1d4ed8; }

.metric-list { list-style: none; padding: 0; margin-bottom: 1.5rem; }
.metric-list li {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0; border-bottom: 1px solid var(--borde); font-size: 0.95rem;
}
.metric-list li span:first-child { font-weight: 600; color: var(--texto-secundario); }
.severidad-alta { color: var(--rojo-alerta); font-weight: 700; background: #fee2e2; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; }

svg { background: #f9fafb; border-radius: 8px; border: 1px solid var(--borde); width: 100%; margin-top: 10px; }
.linea { stroke: #2ecc71; stroke-width: 4; transition: all 0.3s ease; }
.linea.cortada { stroke: #e74c3c; stroke-dasharray: 8 6; }
.nodo-circulo { fill: var(--blanco); stroke: #2ecc71; stroke-width: 3; transition: all 0.4s ease; }
.nodo-circulo.zona-segura { stroke: #3b82f6; fill: #eff6ff; }
.nodo-circulo.apagado { fill: #f3f4f6; stroke: #9ca3af; opacity: 0.5; }
.nodo-texto { fill: var(--texto-principal); font-size: 12px; font-weight: bold; text-anchor: middle; }
.nodo-dato { fill: var(--texto-secundario); font-size: 10px; text-anchor: middle; }
.nodo-grupo.apagado .nodo-texto, .nodo-grupo.apagado .nodo-dato { opacity: 0.5; fill: #9ca3af; }

.card-vacia { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: var(--texto-secundario); background: #fafafa; border: 2px dashed var(--borde); }
#resultado { display: none; border-left: 6px solid var(--verde-primario); }
.no-print { display: block; }
"""

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>Dominó Rural — S.I.G.E.A</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
  <style>__CSS_AQUI__</style>
</head>
<body>
  <header>
    <div class="header-titulo">
      <h1>🚧 Dominó Rural</h1>
      <span>Certificación de Impacto</span>
    </div>
  </header>

  <div class="container">
    <!-- Visualización del Grafo -->
    <div class="card full-width">
      <h2>1. Topología de Caminos y Establecimientos</h2>
      <div id="leyenda">
        <span class="leyenda-item"><span class="punto verde"></span> Transitable</span>
        <span class="leyenda-item"><span class="punto rojo"></span> Corte Simulado</span>
        <span class="leyenda-item"><span class="punto gris"></span> Aislado</span>
      </div>
      <svg id="diagrama" width="800" height="440" viewBox="0 0 800 440" preserveAspectRatio="xMidYMid meet"></svg>
    </div>

    <!-- Controles -->
    <div class="card">
      <h2>2. Parámetros de Simulación</h2>
      <label for="selectorCamino">¿Qué camino está en riesgo de cortarse?</label>
      <select id="selectorCamino"></select>
      <button id="btnSimular" class="btn-analizar">Ver efecto dominó</button>
      <button id="btnReset" class="btn-reset">Restablecer Red</button>
    </div>

    <!-- Resultados -->
    <div class="card card-vacia" id="card-vacia">
      <svg width="48" height="48" fill="none" stroke="#9ca3af" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/></svg>
      <h3 style="margin-top: 10px; color: var(--texto-principal);">Sin simulaciones activas</h3>
      <p>Selecciona un camino y simula el corte para calcular los daños logísticos.</p>
    </div>

    <div class="card" id="resultado">
      <div id="pdf-header" style="display:none; text-align: center; margin-bottom: 20px;">
        <h1 style="color: var(--verde-oscuro); margin: 0; font-size: 1.4rem;">Reporte de Impacto Logístico</h1>
        <p style="color: var(--texto-secundario); font-size: 0.85rem;">Emitido por Dominó Rural</p>
        <hr style="border: 0; border-top: 1px solid #ccc; margin: 15px 0;">
      </div>

      <h2>3. Reporte de Daños y Aislamiento</h2>
      <p style="font-size: 0.9rem; color: var(--texto-secundario); margin-bottom: 1rem;">
        Corte en: <strong id="res-camino-nombre" style="color: var(--texto-principal);"></strong>
      </p>
      <ul class="metric-list">
        <li><span>Establecimientos aislados:</span> <span id="res-est" class="severidad-alta">0</span></li>
        <li><span>Cabezas de ganado sin salida:</span> <span id="res-vacas" style="font-weight: 600;">0</span></li>
        <li><span>Toneladas bloqueadas:</span> <span id="res-ton" style="font-weight: 600;">0</span></li>
        <li><span>Camiones varados:</span> <span id="res-cam" style="font-weight: 600;">0</span></li>
      </ul>
      <button class="btn-success no-print" id="btn-pdf" onclick="generarPDF()">
        📄 Generar Declaración de Impacto (PDF)
      </button>
    </div>
  </div>

  <script>
    const API = window.location.origin;
    let grafo = null;
    let posiciones = {};

    function calcularPosiciones(g) {
      const adyacencia = new Map();
      g.nodos.forEach(function(n) { adyacencia.set(n.id, []); });
      g.caminos.forEach(function(c) {
        adyacencia.get(c.desde).push(c.hasta);
        adyacencia.get(c.hasta).push(c.desde);
      });

      const nivel = new Map([['zona-segura', 0]]);
      const cola = ['zona-segura'];
      while (cola.length > 0) {
        const actual = cola.shift();
        const vecinos = adyacencia.get(actual) || [];
        for (let i = 0; i < vecinos.length; i++) {
          const vecino = vecinos[i];
          if (!nivel.has(vecino)) {
            nivel.set(vecino, nivel.get(actual) + 1);
            cola.push(vecino);
          }
        }
      }

      const porNivel = {};
      g.nodos.forEach(function(n) {
        const l = nivel.has(n.id) ? nivel.get(n.id) : 0;
        if (!porNivel[l]) porNivel[l] = [];
        porNivel[l].push(n.id);
      });

      const pos = {};
      Object.keys(porNivel).forEach(function(l) {
        const ids = porNivel[l];
        const y = 70 + Number(l) * 150;
        const paso = 780 / (ids.length + 1);
        ids.forEach(function(id, i) {
          pos[id] = { x: paso * (i + 1) + 10, y: y };
        });
      });
      return pos;
    }

    function ordenarPorCascada(g, idCaminoCortado, idsAislados) {
      let camino = null;
      for (let i = 0; i < g.caminos.length; i++) {
        if (g.caminos[i].id === idCaminoCortado) { camino = g.caminos[i]; break; }
      }
      if (!camino) return idsAislados;

      const adyacencia = new Map();
      g.nodos.forEach(function(n) { adyacencia.set(n.id, []); });
      g.caminos.forEach(function(c) {
        if (c.id === idCaminoCortado) return;
        adyacencia.get(c.desde).push(c.hasta);
        adyacencia.get(c.hasta).push(c.desde);
      });

      const distancia = new Map([[camino.hasta, 0]]);
      const cola = [camino.hasta];
      while (cola.length > 0) {
        const actual = cola.shift();
        const vecinos = adyacencia.get(actual) || [];
        for (let i = 0; i < vecinos.length; i++) {
          const vecino = vecinos[i];
          if (!distancia.has(vecino)) {
            distancia.set(vecino, distancia.get(actual) + 1);
            cola.push(vecino);
          }
        }
      }

      const copia = idsAislados.slice();
      copia.sort(function(a, b) {
        const da = distancia.has(a) ? distancia.get(a) : 99;
        const db = distancia.has(b) ? distancia.get(b) : 99;
        return da - db;
      });
      return copia;
    }

    async function cargarGrafo() {
      const res = await fetch(API + '/api/grafo');
      grafo = await res.json();
      posiciones = calcularPosiciones(grafo);

      const selector = document.getElementById('selectorCamino');
      let opciones = '';
      grafo.caminos.forEach(function(c) {
        opciones += '<option value="' + c.id + '">' + (c.nombre || c.id) + ' (' + c.desde + ' → ' + c.hasta + ')</option>';
      });
      selector.innerHTML = opciones;

      dibujar([], null);
    }

    function dibujar(idsAislados, idCaminoCortado) {
      const svg = document.getElementById('diagrama');
      let contenido = '';

      grafo.caminos.forEach(function(c) {
        const desde = posiciones[c.desde];
        const hasta = posiciones[c.hasta];
        if (!desde || !hasta) return;
        const cortada = (c.id === idCaminoCortado) ? 'cortada' : '';
        contenido += '<line class="linea ' + cortada + '" x1="' + desde.x + '" y1="' + desde.y + '" x2="' + hasta.x + '" y2="' + hasta.y + '" />';
      });

      grafo.nodos.forEach(function(n) {
        const pos = posiciones[n.id];
        if (!pos) return;
        const esZonaSegura = n.id === 'zona-segura';
        const apagado = idsAislados.indexOf(n.id) !== -1;
        const claseNodo = ['nodo-circulo', esZonaSegura ? 'zona-segura' : '', apagado ? 'apagado' : ''].join(' ');
        const claseGrupo = ['nodo-grupo', apagado ? 'apagado' : ''].join(' ');
        const nombreCorto = n.nombre.split(' ').slice(0, 2).join(' ');

        contenido += '<g class="' + claseGrupo + '">';
        contenido += '<circle class="' + claseNodo + '" cx="' + pos.x + '" cy="' + pos.y + '" r="44" />';
        contenido += '<text class="nodo-texto" x="' + pos.x + '" y="' + (pos.y - 20) + '">' + nombreCorto + '</text>';
        if (!esZonaSegura) {
          contenido += '<text class="nodo-dato" x="' + pos.x + '" y="' + (pos.y - 4) + '">🐄 ' + n.cabezasGanado + '</text>';
          contenido += '<text class="nodo-dato" x="' + pos.x + '" y="' + (pos.y + 9) + '">🌾 ' + n.toneladasProduccion + ' tn</text>';
          contenido += '<text class="nodo-dato" x="' + pos.x + '" y="' + (pos.y + 22) + '">🚛 ' + n.camiones + ' camión</text>';
        } else {
          contenido += '<text class="nodo-dato" x="' + pos.x + '" y="' + (pos.y + 6) + '">Zona Segura</text>';
        }
        contenido += '</g>';
      });
      svg.innerHTML = contenido;
    }

    async function simular() {
      const idCamino = document.getElementById('selectorCamino').value;
      const res = await fetch(API + '/api/simular-corte', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idCamino: idCamino })
      });
      
      const resultado = await res.json();
      const idsAislados = resultado.establecimientosAislados.map(function(e) { return e.id; });
      dibujar([], idCamino);

      const orden = ordenarPorCascada(grafo, idCamino, idsAislados);
      const acumulados = [];
      
      document.getElementById('card-vacia').style.display = 'none';
      document.getElementById('resultado').style.display = 'none';

      orden.forEach(function(id, i) {
        setTimeout(function() {
          acumulados.push(id);
          dibujar(acumulados, idCamino);
        }, (i + 1) * 500);
      });

      setTimeout(function() {
        document.getElementById('resultado').style.display = 'block';
        document.getElementById('res-camino-nombre').innerText = idCamino;
        document.getElementById('res-est').innerText = resultado.establecimientosAislados.length;
        document.getElementById('res-vacas').innerText = resultado.totalCabezasGanado;
        document.getElementById('res-ton').innerText = resultado.totalToneladas;
        document.getElementById('res-cam').innerText = resultado.totalCamiones;
      }, (orden.length + 1) * 500);
    }

    function reset() {
      dibujar([], null);
      document.getElementById('card-vacia').style.display = 'flex';
      document.getElementById('resultado').style.display = 'none';
    }

    function generarPDF() {
      document.getElementById('pdf-header').style.display = 'block';
      document.getElementById('btn-pdf').style.display = 'none';
      const elemento = document.getElementById('resultado');
      const opciones = {
        margin: 15, filename: 'Domino_Rural_Impacto.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };
      html2pdf().set(opciones).from(elemento).save().then(() => {
        document.getElementById('pdf-header').style.display = 'none';
        document.getElementById('btn-pdf').style.display = 'block';
      });
    }

    document.getElementById('btnSimular').addEventListener('click', simular);
    document.getElementById('btnReset').addEventListener('click', reset);
    cargarGrafo();
  </script>
</body>
</html>"""

def obtener_html() -> str:
    """Devuelve la página HTML con los estilos CSS incorporados."""
    return HTML.replace("__CSS_AQUI__", CSS)