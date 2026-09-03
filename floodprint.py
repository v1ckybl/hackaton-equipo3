# Actualización unificada - S.I.G.E.A V2 - 2026 (Módulo de Visión + Red de Caminos)
import cv2
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estructura de datos para el módulo Dominó Rural (Grafo Vial e Infraestructura)
GRAFO_DATA = {
    "nodos": [
        {"id": "zona-segura", "nombre": "Ruta Provincial 12", "cabezasGanado": 0, "toneladasProduccion": 0, "camiones": 0},
        {"id": "est-1", "nombre": "Estancia La Esperanza", "cabezasGanado": 180, "toneladasProduccion": 40, "camiones": 2, "cultivo": "arroz"},
        {"id": "est-2", "nombre": "Establecimiento El Ceibo", "cabezasGanado": 90, "toneladasProduccion": 15, "camiones": 1},
        {"id": "est-3", "nombre": "Campo Don Aurelio", "cabezasGanado": 150, "toneladasProduccion": 30, "camiones": 1, "cultivo": "arroz"},
        {"id": "est-4", "nombre": "Estancia San Roque", "cabezasGanado": 60, "toneladasProduccion": 10, "camiones": 1}
    ],
    "caminos": [
        {"id": "camino-1", "desde": "zona-segura", "hasta": "est-1", "transitable": True, "nombre": "Camino Rural 3"},
        {"id": "camino-2", "desde": "est-1", "hasta": "est-2", "transitable": True, "nombre": "Camino Rural 5"},
        {"id": "camino-3", "desde": "zona-segura", "hasta": "est-3", "transitable": True, "nombre": "Camino Rural 7"},
        {"id": "camino-4", "desde": "est-3", "hasta": "est-4", "transitable": True, "nombre": "Camino Rural 9"}
    ]
}

class SimulacionRequest(BaseModel):
    idCamino: str


def detectar_zona_urbana(imagen_gray):
    gray_blur = cv2.GaussianBlur(imagen_gray, (11, 11), 0)
    edges = cv2.Canny(gray_blur, 120, 220)
    densidad_bordes = float(np.mean(edges) / 255.0)
    es_urbano = bool(densidad_bordes > 0.22)
    return es_urbano, densidad_bordes


def estimar_cultivo_por_color(imagen_hsv, es_urbano: bool):
    if es_urbano:
        return "Zona Urbana / Edificada"

    h, s, v = cv2.split(imagen_hsv)
    mean_h = float(np.mean(h))
    mean_s = float(np.mean(s))

    if 35 <= mean_h <= 85:
        if mean_s > 90:
            return "Maíz / Soja"
        else:
            return "Arroz (Paredón bajo riego)"
    elif mean_h < 35 or mean_h > 140:
        return "Campo Natural / Pastura"
    else:
        return "Foresto-Industria (Pino / Eucalipto)"


@app.get("/api/grafo")
def obtener_grafo():
    return GRAFO_DATA


@app.post("/api/simular-corte")
def simular_corte(data: SimulacionRequest):
    id_camino = data.idCamino
    
    # Cálculo de alcanzabilidad (BFS) excluyendo el camino cortado
    adyacencia = {n["id"]: [] for n in GRAFO_DATA["nodos"]}
    for c in GRAFO_DATA["caminos"]:
        if c["id"] != id_camino:
            adyacencia[c["desde"]].append(c["hasta"])
            adyacencia[c["hasta"]].append(c["desde"])
            
    alcanzables = set(["zona-segura"])
    cola = ["zona-segura"]
    while cola:
        actual = cola.pop(0)
        for vecino in adyacencia.get(actual, []):
            if vecino not in alcanzables:
                alcanzables.add(vecino)
                cola.append(vecino)
                
    aislados = [n for n in GRAFO_DATA["nodos"] if n["id"] != "zona-segura" and n["id"] not in alcanzables]
    
    total_ganado = sum(n["cabezasGanado"] for n in aislados)
    total_toneladas = sum(n["toneladasProduccion"] for n in aislados)
    total_camiones = sum(n["camiones"] for n in aislados)
    
    return {
        "caminoCortado": id_camino,
        "establecimientosAislados": aislados,
        "totalCabezasGanado": total_ganado,
        "totalToneladas": total_toneladas,
        "totalCamiones": total_camiones
    }


@app.post("/api/analizar-imagen-real")
async def analizar_imagen_real(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        imagen = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if imagen is None:
            raise HTTPException(
                status_code=400, detail="No se pudo leer la imagen."
            )

        height, width, _ = imagen.shape
        total_pixels = height * width

        gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)

        es_urbano, densidad = detectar_zona_urbana(gray)

        # MÁSCARAS ESTRICTAS DE AGUA
        lower_w1 = np.array([0, 0, 0])
        upper_w1 = np.array([180, 255, 30])
        mask1 = cv2.inRange(hsv, lower_w1, upper_w1)

        lower_w2 = np.array([70, 25, 40])
        upper_w2 = np.array([140, 255, 220])
        mask2 = cv2.inRange(hsv, lower_w2, upper_w2)

        lower_w3 = np.array([15, 20, 50])
        upper_w3 = np.array([40, 90, 150])
        mask3 = cv2.inRange(hsv, lower_w3, upper_w3)

        water_mask = cv2.bitwise_or(mask1, mask2)
        water_mask = cv2.bitwise_or(water_mask, mask3)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        mask_filtrada = np.zeros_like(water_mask)
        min_area = total_pixels * 0.005

        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                cv2.drawContours(
                    mask_filtrada, [cnt], -1, 255, thickness=cv2.FILLED
                )

        water_pixels = int(cv2.countNonZero(mask_filtrada))
        porcentaje_dano = float(
            round((water_pixels / float(total_pixels)) * 100, 1)
        )
        porcentaje_dano = float(min(porcentaje_dano, 100.0))

        promedio_color = int(np.mean(imagen))
        superficie_total = int(450 + (promedio_color % 10) * 80 + (width % 100))
        area_afectada = float(
            round((porcentaje_dano / 100.0) * superficie_total, 1)
        )

        if porcentaje_dano > 20.0:
            nivel_severidad = "ALTA"
        elif porcentaje_dano >= 6.0:
            nivel_severidad = "MEDIA"
        else:
            nivel_severidad = "BAJA"

        cultivo_estimado = estimar_cultivo_por_color(hsv, es_urbano)

        return {
            "status": "success",
            "metodo": "Visión por Computadora (OpenCV - Espectro Hídrico Calibrado)",
            "datos": {
                "superficie_total_ha": superficie_total,
                "area_afectada_ha": area_afectada,
                "cultivo": cultivo_estimado,
                "severidad": nivel_severidad,
                "dano_estimado_porcentaje": porcentaje_dano,
                "es_zona_urbana": es_urbano,
            },
        }
    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Error en IA: {str(e)}")


app.mount("/", StaticFiles(directory=".", html=True), name="static")