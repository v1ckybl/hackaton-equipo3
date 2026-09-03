"""Tipos de datos del módulo Dominó Rural."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Establecimiento:
    """Representa un establecimiento rural."""

    id: str
    nombre: str
    cabezas_ganado: int
    toneladas_produccion: int
    camiones: int
    cultivo: str | None = None


@dataclass
class Camino:
    """Representa un tramo bidireccional de camino."""

    id: str
    desde: str
    hasta: str
    transitable: bool
    nombre: str | None = None


@dataclass
class Grafo:
    """Red formada por establecimientos y caminos."""

    nodos: list[Establecimiento]
    caminos: list[Camino]


@dataclass
class ResultadoAislamiento:
    """Resultado de simular el corte de un camino."""

    camino_cortado: str
    establecimientos_aislados: list[Establecimiento]
    total_cabezas_ganado: int
    total_toneladas: int
    total_camiones: int


def establecimiento_a_dict(establecimiento: Establecimiento) -> dict:
    """Convierte un establecimiento al formato que esperaba TypeScript."""

    datos = {
        "id": establecimiento.id,
        "nombre": establecimiento.nombre,
        "cabezasGanado": establecimiento.cabezas_ganado,
        "toneladasProduccion": establecimiento.toneladas_produccion,
        "camiones": establecimiento.camiones,
    }

    if establecimiento.cultivo is not None:
        datos["cultivo"] = establecimiento.cultivo

    return datos


def camino_a_dict(camino: Camino) -> dict:
    """Convierte un camino al formato que esperaba TypeScript."""

    datos = {
        "id": camino.id,
        "desde": camino.desde,
        "hasta": camino.hasta,
        "transitable": camino.transitable,
    }

    if camino.nombre is not None:
        datos["nombre"] = camino.nombre

    return datos


def grafo_a_dict(grafo: Grafo) -> dict:
    """Convierte el grafo completo al formato JSON de la API original."""

    return {
        "nodos": [establecimiento_a_dict(nodo) for nodo in grafo.nodos],
        "caminos": [camino_a_dict(camino) for camino in grafo.caminos],
    }


def resultado_a_dict(resultado: ResultadoAislamiento) -> dict:
    """Convierte el resultado de una simulación al formato de la API."""

    return {
        "caminoCortado": resultado.camino_cortado,
        "establecimientosAislados": [
            establecimiento_a_dict(nodo)
            for nodo in resultado.establecimientos_aislados
        ],
        "totalCabezasGanado": resultado.total_cabezas_ganado,
        "totalToneladas": resultado.total_toneladas,
        "totalCamiones": resultado.total_camiones,
    }
