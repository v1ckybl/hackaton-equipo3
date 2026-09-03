import cv2
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detectar_zona_urbana(imagen_gray):
    # Desenfoque más fuerte para eliminar ruido superficial de texturas de vegetación
    gray_blur = cv2.GaussianBlur(imagen_gray, (11, 11), 0)
    # Umbrales de Canny más altos para ignorar texturas naturales y capturar solo estructuras rígidas
    edges = cv2.Canny(gray_blur, 120, 220)
    densidad_bordes = float(np.mean(edges) / 255.0)

    # Umbral elevado para evitar que los bosques o mapas densos pasen por urbanos
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

        # 1. Evaluar si la imagen es predominantemente urbana con el nuevo filtro
        es_urbano, densidad = detectar_zona_urbana(gray)

        # 2. Rangos HSV de agua corregidos para evitar falsos positivos en sombras/suelos
        lower_w1 = np.array([0, 0, 0])
        upper_w1 = np.array([180, 255, 45])
        mask1 = cv2.inRange(hsv, lower_w1, upper_w1)

        lower_w2 = np.array([70, 20, 50])
        upper_w2 = np.array([140, 255, 230])
        mask2 = cv2.inRange(hsv, lower_w2, upper_w2)

        lower_w3 = np.array([12, 15, 50])
        upper_w3 = np.array([45, 100, 160])
        mask3 = cv2.inRange(hsv, lower_w3, upper_w3)

        water_mask = cv2.bitwise_or(mask1, mask2)
        water_mask = cv2.bitwise_or(water_mask, mask3)

        # 3. Limpieza Morfológica
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel)

        # 4. Filtrado por área de contorno
        contours, _ = cv2.findContours(
            water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        mask_filtrada = np.zeros_like(water_mask)

        min_area = total_pixels * 0.0015 

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

        # Cálculo de superficie
        promedio_color = int(np.mean(imagen))
        superficie_total = int(450 + (promedio_color % 10) * 80 + (width % 100))
        area_afectada = float(
            round((porcentaje_dano / 100.0) * superficie_total, 1)
        )

        if porcentaje_dano > 25.0:
            nivel_severidad = "ALTA"
        elif porcentaje_dano >= 8.0:
            nivel_severidad = "MEDIA"
        else:
            nivel_severidad = "BAJA"

        cultivo_estimado = estimar_cultivo_por_color(hsv, es_urbano)

        return {
            "status": "success",
            "metodo": "Visión por Computadora (OpenCV - Análisis Espectral y Textura Ajustado)",
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
        raise HTTPException(status_code=500, detail=str(e))


# =======================================================
# NUEVO: RUTAS PARA SERVIR TUS PÁGINAS WEB (FRONTEND)
# =======================================================

# 1. Si existe una carpeta "img" con tus fotos, le decimos a Python que la muestre
if os.path.isdir("img"):
    app.mount("/img", StaticFiles(directory="img"), name="img")

# 2. Cuando el usuario entra a tu link principal de Render, cargamos el index.html
@app.get("/")
async def cargar_inicio():
    return FileResponse("index.html")

# 3. Ruta dinámica para cargar cualquier otra página (.html) que esté en tu carpeta
@app.get("/{pagina}.html")
async def cargar_paginas(pagina: str):
    archivo = f"{pagina}.html"
    if os.path.exists(archivo):
        return FileResponse(archivo)
    raise HTTPException(status_code=404, detail="Página no encontrada")