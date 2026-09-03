import { Grafo, Camino, Establecimiento, ResultadoAislamiento } from './types';

const NODO_ZONA_SEGURA = 'zona-segura';

/**
 * A partir del grafo completo, arma un mapa de adyacencia
 * (id de nodo -> lista de ids vecinos), considerando SOLO
 * los caminos marcados como transitables.
 */
function construirAdyacencia(grafo: Grafo): Map<string, string[]> {
  const adyacencia = new Map<string, string[]>();

  for (const nodo of grafo.nodos) {
    adyacencia.set(nodo.id, []);
  }

  for (const camino of grafo.caminos) {
    if (!camino.transitable) continue; // ignoramos los cortados
    adyacencia.get(camino.desde)?.push(camino.hasta);
    adyacencia.get(camino.hasta)?.push(camino.desde); // caminos son bidireccionales
  }

  return adyacencia;
}

/**
 * BFS desde la zona segura: devuelve el set de ids de nodos
 * que SÍ son alcanzables con el estado actual de caminos.
 */
function nodosAlcanzables(grafo: Grafo): Set<string> {
  const adyacencia = construirAdyacencia(grafo);
  const visitados = new Set<string>([NODO_ZONA_SEGURA]);
  const cola: string[] = [NODO_ZONA_SEGURA];

  while (cola.length > 0) {
    const actual = cola.shift()!;
    for (const vecino of adyacencia.get(actual) ?? []) {
      if (!visitados.has(vecino)) {
        visitados.add(vecino);
        cola.push(vecino);
      }
    }
  }

  return visitados;
}

/**
 * Simula cortar un camino específico y devuelve qué establecimientos
 * quedan aislados, con el impacto productivo sumado.
 */
export function simularCorte(grafo: Grafo, idCamino: string): ResultadoAislamiento {
  // clonamos el grafo y marcamos ese camino como no transitable,
  // así no mutamos el original
  const grafoSimulado: Grafo = {
    nodos: grafo.nodos,
    caminos: grafo.caminos.map((c) =>
      c.id === idCamino ? { ...c, transitable: false } : c
    ),
  };

  const alcanzables = nodosAlcanzables(grafoSimulado);

  const aislados = grafo.nodos.filter(
    (n) => n.id !== NODO_ZONA_SEGURA && !alcanzables.has(n.id)
  );

  return {
    caminoCortado: idCamino,
    establecimientosAislados: aislados,
    totalCabezasGanado: aislados.reduce((sum, e) => sum + e.cabezasGanado, 0),
    totalToneladas: aislados.reduce((sum, e) => sum + e.toneladasProduccion, 0),
    totalCamiones: aislados.reduce((sum, e) => sum + e.camiones, 0),
  };
}

/**
 * Corre la simulación para TODOS los caminos y devuelve
 * solo los que causan aislamiento, ordenados por impacto
 * (mayor cantidad de ganado primero). Esto es el "diferencial":
 * el sistema prioriza automáticamente qué caminos son críticos.
 */
export function detectarCaminosCriticos(grafo: Grafo): ResultadoAislamiento[] {
  return grafo.caminos
    .map((camino) => simularCorte(grafo, camino.id))
    .filter((resultado) => resultado.establecimientosAislados.length > 0)
    .sort((a, b) => b.totalCabezasGanado - a.totalCabezasGanado);
}