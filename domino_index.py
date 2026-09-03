"""Punto de entrada para probar Dominó Rural desde la terminal."""

from dataclasses import asdict
from pprint import pprint

from domino_data import grafo_ejemplo
from domino_graph import detectar_caminos_criticos, simular_corte


def ejecutar_demo() -> None:
    """Ejecuta las mismas pruebas que el index.ts original."""

    pprint(asdict(simular_corte(grafo_ejemplo, "camino-1")))
    print("---")
    pprint([asdict(resultado) for resultado in detectar_caminos_criticos(grafo_ejemplo)])


if __name__ == "__main__":
    ejecutar_demo()
