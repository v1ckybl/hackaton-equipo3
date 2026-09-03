"""Lógica de simulación del efecto dominó rural."""

from __future__ import annotations

from collections import deque
from dataclasses import replace

from domino_types import Grafo, ResultadoAislamiento


NODO_ZONA_SEGURA = "zona-segura"


def construir_adyacencia(grafo: Grafo) -> dict[str, list[str]]:
    """Construye la lista de vecinos usando solo caminos transitables."""

    adyacencia = {nodo.id: [] for nodo in grafo.nodos}

    for camino in grafo.caminos:
        if not camino.transitable:
            continue

        adyacencia[camino.desde].append(camino.hasta)
        adyacencia[camino.hasta].append(camino.desde)

    return adyacencia


def nodos_alcanzables(grafo: Grafo) -> set[str]:
    """Devuelve los nodos que siguen conectados con la zona segura."""

    adyacencia = construir_adyacencia(grafo)
    visitados = {NODO_ZONA_SEGURA}
    cola = deque([NODO_ZONA_SEGURA])

    while cola:
        actual = cola.popleft()

        for vecino in adyacencia.get(actual, []):
            if vecino not in visitados:
                visitados.add(vecino)
                cola.append(vecino)

    return visitados


def simular_corte(grafo: Grafo, id_camino: str) -> ResultadoAislamiento:
    """Simula el corte de un camino y calcula el impacto productivo."""

    grafo_simulado = Grafo(
        nodos=grafo.nodos,
        caminos=[
            replace(camino, transitable=False)
            if camino.id == id_camino
            else camino
            for camino in grafo.caminos
        ],
    )

    alcanzables = nodos_alcanzables(grafo_simulado)
    aislados = [
        nodo
        for nodo in grafo.nodos
        if nodo.id != NODO_ZONA_SEGURA and nodo.id not in alcanzables
    ]

    return ResultadoAislamiento(
        camino_cortado=id_camino,
        establecimientos_aislados=aislados,
        total_cabezas_ganado=sum(nodo.cabezas_ganado for nodo in aislados),
        total_toneladas=sum(nodo.toneladas_produccion for nodo in aislados),
        total_camiones=sum(nodo.camiones for nodo in aislados),
    )


def detectar_caminos_criticos(grafo: Grafo) -> list[ResultadoAislamiento]:
    """Ordena los caminos que generan aislamiento por impacto ganadero."""

    resultados = [
        simular_corte(grafo, camino.id)
        for camino in grafo.caminos
    ]

    resultados = [
        resultado
        for resultado in resultados
        if resultado.establecimientos_aislados
    ]

    return sorted(
        resultados,
        key=lambda resultado: resultado.total_cabezas_ganado,
        reverse=True,
    )
