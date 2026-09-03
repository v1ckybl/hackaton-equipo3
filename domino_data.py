"""Datos de ejemplo para Dominó Rural."""

from domino_types import Camino, Establecimiento, Grafo


# Red de ejemplo preparada para demostrar el efecto cascada.
grafo_ejemplo = Grafo(
    nodos=[
        Establecimiento(
            id="zona-segura",
            nombre="Ruta Provincial 12 (zona segura)",
            cabezas_ganado=0,
            toneladas_produccion=0,
            camiones=0,
        ),
        Establecimiento(
            id="est-1",
            nombre="Estancia La Esperanza",
            cabezas_ganado=180,
            toneladas_produccion=40,
            camiones=2,
            cultivo="arroz",
        ),
        Establecimiento(
            id="est-2",
            nombre="Establecimiento El Ceibo",
            cabezas_ganado=90,
            toneladas_produccion=15,
            camiones=1,
        ),
        Establecimiento(
            id="est-3",
            nombre="Campo Don Aurelio",
            cabezas_ganado=150,
            toneladas_produccion=30,
            camiones=1,
            cultivo="arroz",
        ),
        Establecimiento(
            id="est-4",
            nombre="Estancia San Roque",
            cabezas_ganado=60,
            toneladas_produccion=10,
            camiones=1,
        ),
    ],
    caminos=[
        Camino(
            id="camino-1",
            desde="zona-segura",
            hasta="est-1",
            transitable=True,
            nombre="Camino Rural 3",
        ),
        Camino(
            id="camino-2",
            desde="est-1",
            hasta="est-2",
            transitable=True,
            nombre="Camino Rural 5",
        ),
        Camino(
            id="camino-3",
            desde="zona-segura",
            hasta="est-3",
            transitable=True,
            nombre="Camino Rural 7",
        ),
        Camino(
            id="camino-4",
            desde="est-3",
            hasta="est-4",
            transitable=True,
            nombre="Camino Rural 9",
        ),
    ],
)
