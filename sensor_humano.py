"""
Sensor Humano - Aplicacion offline
==================================

La aplicacion permite crear reportes aunque el celular no tenga internet.
Los reportes se guardan localmente en un archivo JSON y quedan con estado
"pendiente". Cuando vuelve internet, se pueden sincronizar con el servidor.

No necesita instalar librerias externas.

Uso:

    python sensor_humano.py
        Ejecuta una demostracion completa.

    python sensor_humano.py servidor
        Inicia el servidor central en http://127.0.0.1:8000.

    python sensor_humano.py reportar
        Permite cargar un reporte desde la terminal.

La parte que guarda datos localmente representa el almacenamiento del celular.
La parte HTTP representa el servidor al que se sincroniza la informacion
cuando el dispositivo vuelve a tener internet.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


TIPOS_EVENTO = {
    "agua_camino",
    "camino_cortado",
    "animales_aislados",
    "produccion_afectada",
    "otro",
}

GRAVEDADES = {"baja", "media", "alta", "critica"}


def ahora() -> str:
    """Devuelve la fecha y hora actual en formato ISO."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def generar_id() -> str:
    """Genera un codigo unico para que el reporte no se duplique."""
    return "SR-" + uuid4().hex[:10].upper()


@dataclass
class Reporte:
    """Representa un reporte creado por un productor."""

    productor_id: str
    tipo_evento: str
    gravedad: str
    latitud: float
    longitud: float
    descripcion: str = ""
    foto: Optional[str] = None
    id: str = field(default_factory=generar_id)
    creado_en: str = field(default_factory=ahora)
    estado: str = "pendiente"
    enviado_en: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.productor_id.strip():
            raise ValueError("El identificador del productor no puede estar vacio.")

        if self.tipo_evento not in TIPOS_EVENTO:
            opciones = ", ".join(sorted(TIPOS_EVENTO))
            raise ValueError(f"Tipo de evento invalido. Opciones: {opciones}")

        if self.gravedad not in GRAVEDADES:
            opciones = ", ".join(sorted(GRAVEDADES))
            raise ValueError(f"Gravedad invalida. Opciones: {opciones}")

        self.latitud = float(self.latitud)
        self.longitud = float(self.longitud)

        if not -90 <= self.latitud <= 90:
            raise ValueError("La latitud debe estar entre -90 y 90.")

        if not -180 <= self.longitud <= 180:
            raise ValueError("La longitud debe estar entre -180 y 180.")

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> "Reporte":
        campos_validos = {
            "productor_id",
            "tipo_evento",
            "gravedad",
            "latitud",
            "longitud",
            "descripcion",
            "foto",
            "id",
            "creado_en",
            "estado",
            "enviado_en",
        }
        datos_limpios = {
            clave: valor for clave, valor in datos.items() if clave in campos_validos
        }
        return cls(**datos_limpios)


class AlmacenamientoLocal:
    """Guarda reportes en el celular.

    En este prototipo se representa con un archivo JSON. En una app movil real
    podria reemplazarse por SQLite o una base local del telefono.
    """

    def __init__(self, archivo: Optional[str] = None) -> None:
        self.archivo = Path(archivo) if archivo else None
        self._datos: dict[str, dict[str, Any]] = {}
        self._cargar()

    def _cargar(self) -> None:
        if self.archivo is None or not self.archivo.exists():
            return

        try:
            contenido = json.loads(self.archivo.read_text(encoding="utf-8"))
            self._datos = {
                item["id"]: item
                for item in contenido
                if isinstance(item, dict) and "id" in item
            }
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"No se pudo leer el almacenamiento local: {error}") from error

    def _guardar_archivo(self) -> None:
        if self.archivo is None:
            return

        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        self.archivo.write_text(
            json.dumps(list(self._datos.values()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def guardar(self, reporte: Reporte) -> None:
        self._datos[reporte.id] = reporte.como_dict()
        self._guardar_archivo()

    def obtener(self, reporte_id: str) -> Optional[Reporte]:
        datos = self._datos.get(reporte_id)
        return Reporte.desde_dict(datos) if datos else None

    def todos(self) -> list[Reporte]:
        return [Reporte.desde_dict(datos) for datos in self._datos.values()]

    def pendientes(self) -> list[Reporte]:
        return [reporte for reporte in self.todos() if reporte.estado == "pendiente"]


class SensorHumanoOffline:
    """Logica que usaria la aplicacion del celular."""

    def __init__(self, archivo_local: Optional[str] = "datos/reportes_locales.json") -> None:
        self.almacenamiento = AlmacenamientoLocal(archivo_local)

    def crear_reporte(
        self,
        productor_id: str,
        tipo_evento: str,
        gravedad: str,
        latitud: float,
        longitud: float,
        descripcion: str = "",
        foto: Optional[str] = None,
    ) -> Reporte:
        """Crea y guarda un reporte sin necesitar internet."""
        reporte = Reporte(
            productor_id=productor_id,
            tipo_evento=tipo_evento,
            gravedad=gravedad,
            latitud=latitud,
            longitud=longitud,
            descripcion=descripcion,
            foto=foto,
        )
        self.almacenamiento.guardar(reporte)
        return reporte

    def reportes_pendientes(self) -> list[Reporte]:
        return self.almacenamiento.pendientes()

    def sincronizar_con_servidor_local(self, servidor: "ServidorSensorHumano") -> int:
        """Sincroniza con un servidor en memoria para probar el funcionamiento."""
        pendientes = self.reportes_pendientes()
        ids_recibidos = servidor.recibir_reportes(pendientes)

        for reporte_id in ids_recibidos:
            reporte = self.almacenamiento.obtener(reporte_id)
            if reporte:
                reporte.estado = "enviado"
                reporte.enviado_en = ahora()
                self.almacenamiento.guardar(reporte)

        return len(ids_recibidos)

    def sincronizar_por_internet(self, url_servidor: str, timeout: int = 10) -> int:
        """Manda los reportes pendientes a un servidor HTTP."""
        pendientes = self.reportes_pendientes()

        if not pendientes:
            return 0

        cuerpo = json.dumps(
            {"reportes": [reporte.como_dict() for reporte in pendientes]},
            ensure_ascii=False,
        ).encode("utf-8")

        solicitud = urllib.request.Request(
            url_servidor.rstrip("/") + "/api/sincronizar",
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(solicitud, timeout=timeout) as respuesta:
                resultado = json.loads(respuesta.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ConnectionError(
                "No se pudo sincronizar. Los reportes siguen guardados localmente."
            ) from error

        ids_recibidos = resultado.get("ids_recibidos", [])

        for reporte_id in ids_recibidos:
            reporte = self.almacenamiento.obtener(reporte_id)
            if reporte:
                reporte.estado = "enviado"
                reporte.enviado_en = ahora()
                self.almacenamiento.guardar(reporte)

        return len(ids_recibidos)


class ServidorSensorHumano:
    """Servidor central que recibe los reportes cuando vuelve internet."""

    def __init__(self, archivo: Optional[str] = None) -> None:
        self.almacenamiento = AlmacenamientoLocal(archivo)

    def recibir_reportes(self, reportes: list[Reporte]) -> list[str]:
        """Recibe un lote y evita guardar dos veces el mismo reporte."""
        ids_recibidos: list[str] = []

        for reporte in reportes:
            if self.almacenamiento.obtener(reporte.id) is None:
                reporte.estado = "recibido"
                self.almacenamiento.guardar(reporte)

            ids_recibidos.append(reporte.id)

        return ids_recibidos

    def recibir_json(self, datos: dict[str, Any]) -> list[str]:
        paquetes = datos.get("reportes", [])
        if not isinstance(paquetes, list):
            raise ValueError("El campo 'reportes' debe ser una lista.")

        reportes = [Reporte.desde_dict(paquete) for paquete in paquetes]
        return self.recibir_reportes(reportes)

    def todos_los_reportes(self) -> list[Reporte]:
        return self.almacenamiento.todos()


class ManejadorHTTP(BaseHTTPRequestHandler):
    """API minima para conectar una app o un frontend."""

    server_version = "SensorHumanoOffline/1.0"

    @property
    def aplicacion(self) -> ServidorSensorHumano:
        return self.server.aplicacion_sensor  # type: ignore[attr-defined]

    def responder_json(self, datos: dict[str, Any], codigo: int = 200) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # Permite que el index.html desplegado como Static Site
        # se comunique con este servidor Python.
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

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/reportes":
            reportes = [
                reporte.como_dict()
                for reporte in self.aplicacion.todos_los_reportes()
            ]
            self.responder_json({"reportes": reportes})
            return

        self.responder_json({"error": "Ruta no encontrada."}, 404)

    def do_POST(self) -> None:  # noqa: N802
        try:
            datos = self.leer_json()

            if self.path == "/api/sincronizar":
                ids = self.aplicacion.recibir_json(datos)
                self.responder_json({"ids_recibidos": ids})
                return

            self.responder_json({"error": "Ruta no encontrada."}, 404)

        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            self.responder_json({"error": str(error)}, 400)

    def log_message(self, formato: str, *argumentos: Any) -> None:
        return


def crear_servidor_http(
    aplicacion: ServidorSensorHumano,
    host: str = "127.0.0.1",
    puerto: int = 8000,
) -> HTTPServer:
    servidor = HTTPServer((host, puerto), ManejadorHTTP)
    servidor.aplicacion_sensor = aplicacion  # type: ignore[attr-defined]
    return servidor


def demostracion() -> None:
    """Prueba: se crea offline y luego se sincroniza."""
    print("=== SENSOR HUMANO OFFLINE ===")

    celular = SensorHumanoOffline(archivo_local=None)
    servidor = ServidorSensorHumano()

    reporte = celular.crear_reporte(
        productor_id="PRODUCTOR-001",
        tipo_evento="camino_cortado",
        gravedad="alta",
        latitud=-27.4692,
        longitud=-58.8306,
        descripcion="El agua cubre el camino principal.",
        foto="reporte_001.jpg",
    )

    print("Reporte creado:", reporte.id)
    print("Estado sin internet:", reporte.estado)
    print("Pendientes en el celular:", len(celular.reportes_pendientes()))

    cantidad = celular.sincronizar_con_servidor_local(servidor)
    reporte_actualizado = celular.almacenamiento.obtener(reporte.id)

    print("Reportes sincronizados:", cantidad)
    print("Estado despues de sincronizar:", reporte_actualizado.estado)
    print("Reportes recibidos por el servidor:", len(servidor.todos_los_reportes()))


def pedir_opcion(mensaje: str, opciones: set[str]) -> str:
    while True:
        valor = input(mensaje).strip().lower()
        if valor in opciones:
            return valor
        print("Opcion invalida. Elegi una de:", ", ".join(sorted(opciones)))


def cargar_reporte_desde_terminal() -> None:
    """Permite probar la carga local como si fuera la app del celular."""
    celular = SensorHumanoOffline()

    print("=== NUEVO REPORTE OFFLINE ===")
    productor_id = input("ID del productor: ").strip()
    tipo = pedir_opcion("Tipo de evento: ", TIPOS_EVENTO)
    gravedad = pedir_opcion("Gravedad: ", GRAVEDADES)
    latitud = float(input("Latitud: "))
    longitud = float(input("Longitud: "))
    descripcion = input("Descripcion: ").strip()
    foto = input("Nombre de foto opcional: ").strip() or None

    reporte = celular.crear_reporte(
        productor_id,
        tipo,
        gravedad,
        latitud,
        longitud,
        descripcion,
        foto,
    )

    print("Reporte guardado en el celular.")
    print("Codigo:", reporte.id)
    print("Estado:", reporte.estado)
    print("Se enviara cuando vuelva internet.")


def iniciar_servidor() -> None:
    aplicacion = ServidorSensorHumano("datos/reportes_servidor.json")
    # Render asigna el puerto mediante la variable de entorno PORT.
    # Si se ejecuta localmente, se usa el puerto 8000.
    puerto = int(os.environ.get("PORT", "8000"))
    servidor = crear_servidor_http(aplicacion, "0.0.0.0", puerto)

    print(f"Servidor iniciado en el puerto {puerto}")
    print("Presiona Ctrl+C para detenerlo.")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1].lower() == "servidor":
        iniciar_servidor()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "reportar":
        cargar_reporte_desde_terminal()
    else:
        demostracion()


if __name__ == "__main__":
    main()
