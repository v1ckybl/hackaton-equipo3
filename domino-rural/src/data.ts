import { Grafo } from './types';

// Dataset de ejemplo: un hub central ("zona segura") conectado en cadena
// a varios establecimientos. Armado así a propósito para poder demostrar
// el efecto cascada (cortar un camino aísla más de un establecimiento).
export const grafoEjemplo: Grafo = {
  nodos: [
    { id: 'zona-segura', nombre: 'Ruta Provincial 12 (zona segura)', cabezasGanado: 0, toneladasProduccion: 0, camiones: 0 },
    { id: 'est-1', nombre: 'Estancia La Esperanza', cabezasGanado: 180, toneladasProduccion: 40, camiones: 2, cultivo: 'arroz' },
    { id: 'est-2', nombre: 'Establecimiento El Ceibo', cabezasGanado: 90, toneladasProduccion: 15, camiones: 1 },
    { id: 'est-3', nombre: 'Campo Don Aurelio', cabezasGanado: 150, toneladasProduccion: 30, camiones: 1, cultivo: 'arroz' },
    { id: 'est-4', nombre: 'Estancia San Roque', cabezasGanado: 60, toneladasProduccion: 10, camiones: 1 },
  ],
  caminos: [
    { id: 'camino-1', desde: 'zona-segura', hasta: 'est-1', transitable: true, nombre: 'Camino Rural 3' },
    { id: 'camino-2', desde: 'est-1', hasta: 'est-2', transitable: true, nombre: 'Camino Rural 5' },
    { id: 'camino-3', desde: 'zona-segura', hasta: 'est-3', transitable: true, nombre: 'Camino Rural 7' },
    { id: 'camino-4', desde: 'est-3', hasta: 'est-4', transitable: true, nombre: 'Camino Rural 9' },
  ],
};