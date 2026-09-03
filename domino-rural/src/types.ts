// Representa un establecimiento rural (productor, campo)
export interface Establecimiento {
  id: string;
  nombre: string;
  cabezasGanado: number;
  toneladasProduccion: number;
  camiones: number;
  cultivo?: string; // opcional: no todos tienen cultivo (puede ser solo ganadero)
}

// Representa un tramo de camino que conecta dos puntos de la red
export interface Camino {
  id: string;
  desde: string; // id del nodo origen
  hasta: string; // id del nodo destino
  transitable: boolean;
  nombre?: string;
}

// El grafo completo: nodos (establecimientos + zona segura) y aristas (caminos)
export interface Grafo {
  nodos: Establecimiento[];
  caminos: Camino[];
}

// Lo que devuelve la simulación cuando cortás un camino
export interface ResultadoAislamiento {
  caminoCortado: string;
  establecimientosAislados: Establecimiento[];
  totalCabezasGanado: number;
  totalToneladas: number;
  totalCamiones: number;
}