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


HTML_INDEX = "<!doctype html>\n<html lang=\"es\">\n<head>\n  <meta charset=\"UTF-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n  <meta name=\"theme-color\" content=\"#087f5b\">\n  <link rel=\"manifest\" href=\"manifest.json\">\n  <title>Sensor Humano Rural</title>\n  <style>\n    :root {\n      --verde: #087f5b;\n      --verde-oscuro: #075b43;\n      --verde-claro: #e8f7f1;\n      --fondo: #f4f8f6;\n      --texto: #17352c;\n      --gris: #668077;\n      --borde: #d7e6df;\n      --rojo: #b42318;\n      --amarillo: #a15c00;\n      font-family: Arial, Helvetica, sans-serif;\n    }\n\n    * { box-sizing: border-box; }\n\n    body {\n      margin: 0;\n      background: var(--fondo);\n      color: var(--texto);\n    }\n\n    .contenedor {\n      width: min(1050px, 92%);\n      margin: 0 auto;\n      padding: 28px 0 50px;\n    }\n\n    header {\n      display: flex;\n      align-items: center;\n      justify-content: space-between;\n      gap: 18px;\n      margin-bottom: 22px;\n    }\n\n    h1, h2, p { margin-top: 0; }\n    h1 { margin-bottom: 6px; font-size: clamp(1.65rem, 4vw, 2.35rem); }\n    h2 { margin-bottom: 16px; font-size: 1.25rem; }\n    .subtitulo { color: var(--gris); margin-bottom: 0; }\n\n    .estado {\n      border-radius: 999px;\n      padding: 9px 14px;\n      font-weight: bold;\n      white-space: nowrap;\n      font-size: .9rem;\n    }\n\n    .estado.online { background: #d9f7e9; color: #116b3d; }\n    .estado.offline { background: #fff0d6; color: var(--amarillo); }\n\n    .tarjeta {\n      background: white;\n      border: 1px solid var(--borde);\n      border-radius: 18px;\n      padding: 22px;\n      margin-bottom: 20px;\n      box-shadow: 0 8px 25px rgba(31, 75, 59, .06);\n    }\n\n    .grid { display: grid; gap: 15px; }\n    .grid-dos { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n\n    label {\n      display: block;\n      font-weight: bold;\n      margin-bottom: 7px;\n      font-size: .94rem;\n    }\n\n    input, select, textarea {\n      width: 100%;\n      border: 1px solid var(--borde);\n      border-radius: 10px;\n      padding: 12px;\n      color: var(--texto);\n      background: #fbfefd;\n      font: inherit;\n    }\n\n    textarea { min-height: 90px; resize: vertical; }\n\n    input:focus, select:focus, textarea:focus {\n      outline: 3px solid rgba(8, 127, 91, .15);\n      border-color: var(--verde);\n    }\n\n    .acciones { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }\n\n    button {\n      border: 0;\n      border-radius: 10px;\n      padding: 12px 16px;\n      font: inherit;\n      font-weight: bold;\n      cursor: pointer;\n    }\n\n    .boton-principal { background: var(--verde); color: white; }\n    .boton-principal:hover { background: var(--verde-oscuro); }\n    .boton-secundario { background: var(--verde-claro); color: var(--verde-oscuro); }\n    button:disabled { opacity: .6; cursor: not-allowed; }\n\n    .mensaje {\n      display: none;\n      border-radius: 10px;\n      padding: 12px;\n      margin-top: 15px;\n      font-weight: bold;\n    }\n\n    .mensaje.visible { display: block; }\n    .mensaje.ok { background: #e4f7ed; color: #116b3d; }\n    .mensaje.error { background: #ffebe9; color: var(--rojo); }\n\n    .lista { display: grid; gap: 12px; }\n\n    .reporte {\n      border: 1px solid var(--borde);\n      border-left: 5px solid var(--verde);\n      border-radius: 12px;\n      padding: 14px;\n      background: #fcfffd;\n    }\n\n    .reporte-cabecera {\n      display: flex;\n      justify-content: space-between;\n      gap: 12px;\n      align-items: start;\n    }\n\n    .reporte h3 { margin: 0 0 6px; font-size: 1rem; }\n    .reporte p { margin: 5px 0 0; color: var(--gris); font-size: .92rem; }\n    .etiqueta {\n      background: var(--verde-claro);\n      color: var(--verde-oscuro);\n      border-radius: 999px;\n      padding: 5px 9px;\n      font-size: .78rem;\n      font-weight: bold;\n      white-space: nowrap;\n    }\n\n    .vacio { color: var(--gris); margin-bottom: 0; }\n\n    @media (max-width: 680px) {\n      header { align-items: flex-start; flex-direction: column; }\n      .grid-dos { grid-template-columns: 1fr; }\n      .tarjeta { padding: 17px; }\n    }\n  </style>\n</head>\n<body>\n  <main class=\"contenedor\">\n    <header>\n      <div>\n        <h1>Sensor Humano Rural</h1>\n        <p class=\"subtitulo\">Reportá problemas del campo aunque no tengas internet.</p>\n      </div>\n      <div id=\"estadoConexion\" class=\"estado offline\">Sin internet</div>\n    </header>\n\n    <section class=\"tarjeta\">\n      <h2>Nuevo reporte</h2>\n      <form id=\"formularioReporte\">\n        <div class=\"grid grid-dos\">\n          <div>\n            <label for=\"productorId\">Identificación del productor</label>\n            <input id=\"productorId\" required placeholder=\"Ejemplo: PRODUCTOR-001\">\n          </div>\n\n          <div>\n            <label for=\"tipoEvento\">Tipo de problema</label>\n            <select id=\"tipoEvento\" required>\n              <option value=\"agua_camino\">Agua sobre el camino</option>\n              <option value=\"camino_cortado\">Camino cortado</option>\n              <option value=\"animales_aislados\">Animales aislados</option>\n              <option value=\"produccion_afectada\">Producción afectada</option>\n              <option value=\"otro\">Otro</option>\n            </select>\n          </div>\n\n          <div>\n            <label for=\"gravedad\">Gravedad</label>\n            <select id=\"gravedad\" required>\n              <option value=\"baja\">Baja</option>\n              <option value=\"media\" selected>Media</option>\n              <option value=\"alta\">Alta</option>\n              <option value=\"critica\">Crítica</option>\n            </select>\n          </div>\n\n          <div>\n            <label for=\"foto\">Foto opcional</label>\n            <input id=\"foto\" type=\"file\" accept=\"image/*\">\n          </div>\n\n          <div>\n            <label for=\"latitud\">Latitud</label>\n            <input id=\"latitud\" type=\"number\" step=\"any\" required placeholder=\"Ejemplo: -27.48\">\n          </div>\n\n          <div>\n            <label for=\"longitud\">Longitud</label>\n            <input id=\"longitud\" type=\"number\" step=\"any\" required placeholder=\"Ejemplo: -58.83\">\n          </div>\n        </div>\n\n        <div class=\"acciones\">\n          <button id=\"usarUbicacion\" class=\"boton-secundario\" type=\"button\">Usar mi ubicación</button>\n        </div>\n\n        <div style=\"margin-top: 15px;\">\n          <label for=\"descripcion\">Descripción</label>\n          <textarea id=\"descripcion\" placeholder=\"Contá brevemente qué está pasando...\"></textarea>\n        </div>\n\n        <div class=\"acciones\">\n          <button class=\"boton-principal\" type=\"submit\">Guardar reporte</button>\n          <button id=\"sincronizar\" class=\"boton-secundario\" type=\"button\">Sincronizar pendientes</button>\n        </div>\n\n        <div id=\"mensaje\" class=\"mensaje\"></div>\n      </form>\n    </section>\n\n    <section class=\"tarjeta\">\n      <h2>Reportes guardados en este celular</h2>\n      <div id=\"listaPendientes\" class=\"lista\"></div>\n    </section>\n\n    <section class=\"tarjeta\">\n      <h2>Reportes recibidos por la plataforma</h2>\n      <div id=\"listaServidor\" class=\"lista\"></div>\n    </section>\n  </main>\n\n  <script>\n    // Esta es la URL del servidor Python que ya desplegaste en Render.\n    const API_URL = window.location.origin;\n    const CLAVE_LOCAL = \"sensor_humano_reportes\";\n\n    let reportes = cargarReportesLocales();\n\n    function cargarReportesLocales() {\n      try {\n        return JSON.parse(localStorage.getItem(CLAVE_LOCAL) || \"[]\");\n      } catch (error) {\n        return [];\n      }\n    }\n\n    function guardarReportesLocales() {\n      localStorage.setItem(CLAVE_LOCAL, JSON.stringify(reportes));\n    }\n\n    function generarId() {\n      if (window.crypto && crypto.randomUUID) {\n        return \"SR-\" + crypto.randomUUID().slice(0, 10).toUpperCase();\n      }\n      return \"SR-\" + Date.now().toString(36).toUpperCase();\n    }\n\n    function mostrarMensaje(texto, tipo = \"ok\") {\n      const elemento = document.getElementById(\"mensaje\");\n      elemento.textContent = texto;\n      elemento.className = \"mensaje visible \" + tipo;\n      setTimeout(() => elemento.className = \"mensaje\", 5000);\n    }\n\n    function escapeHtml(texto) {\n      return String(texto || \"\").replace(/[&<>'\"]/g, caracter => ({\n        \"&\": \"&amp;\",\n        \"<\": \"&lt;\",\n        \">\": \"&gt;\",\n        \"'\": \"&#39;\",\n        '\"': \"&quot;\"\n      }[caracter]));\n    }\n\n    function nombreTipo(tipo) {\n      return {\n        agua_camino: \"Agua sobre el camino\",\n        camino_cortado: \"Camino cortado\",\n        animales_aislados: \"Animales aislados\",\n        produccion_afectada: \"Producción afectada\",\n        otro: \"Otro\"\n      }[tipo] || tipo;\n    }\n\n    function tarjetaReporte(reporte, estado) {\n      return `\n        <article class=\"reporte\">\n          <div class=\"reporte-cabecera\">\n            <div>\n              <h3>${escapeHtml(nombreTipo(reporte.tipo_evento))}</h3>\n              <p><strong>Productor:</strong> ${escapeHtml(reporte.productor_id)}</p>\n              <p><strong>Gravedad:</strong> ${escapeHtml(reporte.gravedad)}</p>\n              <p><strong>Ubicación:</strong> ${escapeHtml(reporte.latitud)}, ${escapeHtml(reporte.longitud)}</p>\n              <p><strong>Descripción:</strong> ${escapeHtml(reporte.descripcion) || \"Sin descripción\"}</p>\n            </div>\n            <span class=\"etiqueta\">${escapeHtml(estado)}</span>\n          </div>\n        </article>`;\n    }\n\n    function mostrarReportesLocales() {\n      const elemento = document.getElementById(\"listaPendientes\");\n      const pendientes = reportes.filter(reporte => reporte.estado === \"pendiente\");\n\n      if (pendientes.length === 0) {\n        elemento.innerHTML = '<p class=\"vacio\">No hay reportes pendientes.</p>';\n        return;\n      }\n\n      elemento.innerHTML = pendientes\n        .map(reporte => tarjetaReporte(reporte, \"Pendiente\"))\n        .join(\"\");\n    }\n\n    function actualizarEstadoConexion() {\n      const elemento = document.getElementById(\"estadoConexion\");\n      const conectado = navigator.onLine;\n      elemento.textContent = conectado ? \"Con internet\" : \"Sin internet\";\n      elemento.className = \"estado \" + (conectado ? \"online\" : \"offline\");\n\n      if (conectado) sincronizarPendientes();\n    }\n\n    function leerFoto(file) {\n      if (!file) return Promise.resolve(null);\n\n      return new Promise((resolve) => {\n        const lector = new FileReader();\n        lector.onload = () => resolve({ nombre: file.name, contenido: lector.result });\n        lector.onerror = () => resolve({ nombre: file.name, contenido: null });\n        lector.readAsDataURL(file);\n      });\n    }\n\n    async function crearReporte(evento) {\n      evento.preventDefault();\n\n      const foto = await leerFoto(document.getElementById(\"foto\").files[0]);\n      const reporte = {\n        id: generarId(),\n        productor_id: document.getElementById(\"productorId\").value.trim(),\n        tipo_evento: document.getElementById(\"tipoEvento\").value,\n        gravedad: document.getElementById(\"gravedad\").value,\n        latitud: Number(document.getElementById(\"latitud\").value),\n        longitud: Number(document.getElementById(\"longitud\").value),\n        descripcion: document.getElementById(\"descripcion\").value.trim(),\n        foto: foto,\n        creado_en: new Date().toISOString(),\n        estado: \"pendiente\",\n        enviado_en: null\n      };\n\n      reportes.push(reporte);\n      guardarReportesLocales();\n      mostrarReportesLocales();\n      document.getElementById(\"formularioReporte\").reset();\n      mostrarMensaje(\"Reporte guardado en el celular. Queda pendiente de envío.\");\n\n      if (navigator.onLine) {\n        await sincronizarPendientes();\n      }\n    }\n\n    async function sincronizarPendientes() {\n      const pendientes = reportes.filter(reporte => reporte.estado === \"pendiente\");\n      if (pendientes.length === 0 || !navigator.onLine) return;\n\n      const boton = document.getElementById(\"sincronizar\");\n      boton.disabled = true;\n\n      try {\n        const respuesta = await fetch(API_URL + \"/api/sincronizar\", {\n          method: \"POST\",\n          headers: { \"Content-Type\": \"application/json\" },\n          body: JSON.stringify({ reportes: pendientes })\n        });\n\n        if (!respuesta.ok) throw new Error(\"El servidor rechazó los reportes.\");\n\n        const datos = await respuesta.json();\n        const idsRecibidos = new Set(datos.ids_recibidos || []);\n\n        reportes = reportes.map(reporte => {\n          if (!idsRecibidos.has(reporte.id)) return reporte;\n          return {\n            ...reporte,\n            estado: \"enviado\",\n            enviado_en: new Date().toISOString()\n          };\n        });\n\n        guardarReportesLocales();\n        mostrarReportesLocales();\n        mostrarMensaje(`${idsRecibidos.size} reporte(s) sincronizado(s) correctamente.`);\n        await cargarReportesDelServidor();\n      } catch (error) {\n        mostrarMensaje(\"No se pudo sincronizar. Los reportes siguen guardados en el celular.\", \"error\");\n      } finally {\n        boton.disabled = false;\n      }\n    }\n\n    async function cargarReportesDelServidor() {\n      const elemento = document.getElementById(\"listaServidor\");\n\n      try {\n        const respuesta = await fetch(API_URL + \"/api/reportes\");\n        if (!respuesta.ok) throw new Error(\"No se pudo consultar el servidor.\");\n        const datos = await respuesta.json();\n        const recibidos = datos.reportes || [];\n\n        elemento.innerHTML = recibidos.length\n          ? recibidos.map(reporte => tarjetaReporte(reporte, \"Recibido\")).join(\"\")\n          : '<p class=\"vacio\">Todavía no hay reportes sincronizados.</p>';\n      } catch (error) {\n        elemento.innerHTML = '<p class=\"vacio\">El servidor no está disponible ahora.</p>';\n      }\n    }\n\n    document.getElementById(\"formularioReporte\").addEventListener(\"submit\", crearReporte);\n    document.getElementById(\"sincronizar\").addEventListener(\"click\", sincronizarPendientes);\n    document.getElementById(\"usarUbicacion\").addEventListener(\"click\", () => {\n      if (!navigator.geolocation) {\n        mostrarMensaje(\"Este dispositivo no permite obtener la ubicación.\", \"error\");\n        return;\n      }\n\n      navigator.geolocation.getCurrentPosition(\n        posicion => {\n          document.getElementById(\"latitud\").value = posicion.coords.latitude.toFixed(6);\n          document.getElementById(\"longitud\").value = posicion.coords.longitude.toFixed(6);\n          mostrarMensaje(\"Ubicación cargada correctamente.\");\n        },\n        () => mostrarMensaje(\"No se pudo obtener la ubicación. También podés escribirla manualmente.\", \"error\")\n      );\n    });\n\n    window.addEventListener(\"online\", actualizarEstadoConexion);\n    window.addEventListener(\"offline\", actualizarEstadoConexion);\n\n    if (\"serviceWorker\" in navigator) {\n      window.addEventListener(\"load\", () => navigator.serviceWorker.register(\"sw.js\"));\n    }\n\n    mostrarReportesLocales();\n    actualizarEstadoConexion();\n    cargarReportesDelServidor();\n  </script>\n</body>\n</html>\n"

SERVICE_WORKER = "const CACHE_NAME = \"sensor-humano-v1\";\nconst ARCHIVOS = [\"/\", \"/index.html\", \"/manifest.json\"];\n\nself.addEventListener(\"install\", event => {\n  event.waitUntil(\n    caches.open(CACHE_NAME).then(cache => cache.addAll(ARCHIVOS))\n  );\n  self.skipWaiting();\n});\n\nself.addEventListener(\"activate\", event => {\n  event.waitUntil(self.clients.claim());\n});\n\nself.addEventListener(\"fetch\", event => {\n  if (event.request.method !== \"GET\") return;\n\n  event.respondWith(\n    caches.match(event.request).then(cached => {\n      if (cached) return cached;\n\n      return fetch(event.request).then(response => {\n        const copia = response.clone();\n        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copia));\n        return response;\n      }).catch(() => caches.match(\"/index.html\"));\n    })\n  );\n});\n"

MANIFEST_JSON = "{\n  \"name\": \"Sensor Humano Rural\",\n  \"short_name\": \"Sensor Humano\",\n  \"start_url\": \"/\",\n  \"display\": \"standalone\",\n  \"background_color\": \"#f4f8f6\",\n  \"theme_color\": \"#087f5b\",\n  \"lang\": \"es\"\n}\n"


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

    def responder_texto(
        self,
        texto: str,
        tipo_contenido: str,
        codigo: int = 200,
    ) -> None:
        cuerpo = texto.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo_contenido)
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
        ruta = self.path.split("?", 1)[0]

        if ruta in {"/", "/index.html"}:
            self.responder_texto(HTML_INDEX, "text/html; charset=utf-8")
            return

        if ruta == "/sw.js":
            self.responder_texto(SERVICE_WORKER, "text/javascript; charset=utf-8")
            return

        if ruta == "/manifest.json":
            self.responder_texto(MANIFEST_JSON, "application/manifest+json")
            return

        if ruta == "/api/reportes":
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
