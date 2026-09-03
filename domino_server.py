"""API HTTP de Dominó Rural, equivalente al server.ts original."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from domino_data import grafo_ejemplo
from domino_graph import detectar_caminos_criticos, simular_corte
from domino_types import grafo_a_dict, resultado_a_dict


class ManejadorDominioRural(BaseHTTPRequestHandler):
    """Expone las rutas de la API para el frontend."""

    server_version = "DominoRuralPython/1.0"

    def enviar_json(self, datos: Any, codigo: int = 200) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")

        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def leer_json(self) -> dict[str, Any]:
        longitud = int(self.headers.get("Content-Length", "0"))
        cuerpo = self.rfile.read(longitud)
        datos = json.loads(cuerpo.decode("utf-8"))

        if not isinstance(datos, dict):
            raise ValueError("El cuerpo debe ser un objeto JSON.")

        return datos

    def do_GET(self) -> None:
        ruta = urlparse(self.path).path

        # 1. Servir el Dashboard Principal S.I.G.E.A (tu index.html)
        if ruta == "/" or ruta == "/index.html":
            try:
                # Asegúrate de que el archivo index.html esté en la misma carpeta en Render
                with open("index.html", "rb") as archivo:
                    cuerpo = archivo.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)
            except FileNotFoundError:
                self.send_error(404, "No se encontró el archivo index.html")
            return

        # 2. Servir la Interfaz de Dominó Rural (generada desde Python)
        if ruta == "/domino":
            # Importamos la función que genera el HTML del simulador (del paso anterior)
            from domino_rural_interfaz import obtener_html
            
            cuerpo = obtener_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
            return

        # 3. Mantener las rutas de la API original intactas
        if ruta == "/api/caminos-criticos":
            resultado = detectar_caminos_criticos(grafo_ejemplo)
            self.enviar_json([resultado_a_dict(item) for item in resultado])
            return

        if ruta == "/api/grafo":
            self.enviar_json(grafo_a_dict(grafo_ejemplo))
            return

        self.enviar_json({"error": "Ruta no encontrada."}, 404)

    def do_POST(self) -> None:  # noqa: N802
        ruta = urlparse(self.path).path

        try:
            datos = self.leer_json()
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self.enviar_json({"error": str(error)}, 400)
            return

        if ruta != "/api/simular-corte":
            self.enviar_json({"error": "Ruta no encontrada."}, 404)
            return

        id_camino = datos.get("idCamino")
        if not isinstance(id_camino, str) or not id_camino:
            self.enviar_json({"error": "Falta el campo idCamino"}, 400)
            return

        existe = any(camino.id == id_camino for camino in grafo_ejemplo.caminos)
        if not existe:
            self.enviar_json(
                {"error": f"No existe el camino {id_camino}"},
                404,
            )
            return

        resultado = simular_corte(grafo_ejemplo, id_camino)
        self.enviar_json(resultado_a_dict(resultado))

    def log_message(self, formato: str, *argumentos: Any) -> None:
        return


def iniciar_servidor() -> None:
    """Inicia la API usando el puerto de Render o el 3002 local."""

    puerto = int(os.environ.get("PORT", "3002"))
    servidor = ThreadingHTTPServer(("0.0.0.0", puerto), ManejadorDominioRural)

    print(f"Dominó Rural corriendo en http://127.0.0.1:{puerto}")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    iniciar_servidor()
