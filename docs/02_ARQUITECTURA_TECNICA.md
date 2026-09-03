# Última Ventana — Arquitectura Técnica

## 1. Objetivo del documento

Este documento define la arquitectura técnica del MVP de **Última Ventana**.

Su propósito es servir como guía de implementación para que backend, frontend, datos, GIS y Machine Learning trabajen sobre una misma estructura.

El sistema debe transformar datos meteorológicos, geoespaciales y satelitales en una predicción de riesgo por tramo de camino y, a partir de ella, calcular una **Última Ventana** de salida recomendada.

---

## 2. Principio de arquitectura

La arquitectura se organiza en cinco bloques principales:

```text
1. Fuentes externas
        ↓
2. Ingesta y procesamiento
        ↓
3. Persistencia geoespacial
        ↓
4. Motor de predicción
        ↓
5. API + frontend
```

El flujo completo es:

```text
Fuentes externas
    ↓
ETL / Ingesta
    ↓
PostgreSQL + PostGIS
    ↓
Feature Engineering
    ↓
Modelo de Machine Learning
    ↓
Predicción de riesgo
    ↓
Cálculo de hora crítica
    ↓
Cálculo de Última Ventana
    ↓
FastAPI
    ↓
Frontend con mapa
    ↓
Alertas y decisión
```

---

## 3. Alcance técnico del MVP

El MVP debe ser capaz de:

- trabajar sobre una región rural acotada de Corrientes;
- cargar caminos georreferenciados;
- dividirlos en segmentos;
- almacenar datos geoespaciales en PostGIS;
- obtener datos meteorológicos externos;
- obtener y procesar información satelital;
- obtener topografía;
- construir features por segmento;
- ejecutar inferencia con un modelo previamente entrenado;
- generar un `risk_score`;
- proyectar riesgo por diferentes horas futuras;
- calcular la hora crítica;
- calcular Última Ventana;
- exponer los resultados mediante una API REST;
- visualizar segmentos sobre un mapa web;
- generar alertas dentro de la aplicación.

---

## 4. Stack tecnológico propuesto

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- GeoAlchemy2

### Base de datos

- PostgreSQL
- PostGIS

### Procesamiento de datos y GIS

- Pandas
- GeoPandas
- Shapely
- Rasterio
- GDAL
- PyProj
- NumPy

### Machine Learning

- Scikit-learn
- XGBoost

### Experimentación

- Jupyter Notebook
- Google Colab

### Frontend

- React
- TypeScript
- Leaflet o MapLibre
- OpenStreetMap como mapa base

### Infraestructura

- Docker
- Docker Compose
- GitHub

---

## 5. Diagrama general

```text
                    ┌───────────────────┐
                    │  FUENTES EXTERNAS │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
       Meteorología       Satélite        Geografía
         SMN / GPM        Sentinel-1      IGN / IDECorr
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    ┌───────────────────┐
                    │ INGESTA / ETL     │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ PostgreSQL        │
                    │ + PostGIS         │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ Feature Pipeline  │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ Modelo ML         │
                    │ XGBoost           │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ Risk Prediction   │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ Última Ventana    │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ FastAPI           │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ React + Mapa      │
                    └───────────────────┘
```

---

## 6. Entidad central: `road_segment`

El elemento central del sistema es el tramo de camino.

Cada camino se divide en segmentos.

Ejemplo:

```text
Camino Rural A

Segmento 1
Segmento 2
Segmento 3
Segmento 4
```

Cada segmento tiene un identificador único:

```text
road_segment_id
```

Este ID conecta:

- geometría;
- datos topográficos;
- datos meteorológicos;
- datos satelitales;
- features;
- predicciones;
- alertas.

Ejemplo conceptual:

```text
road_segment_id = 152
        │
        ├── geometry
        ├── elevation
        ├── slope
        ├── rain_24h
        ├── forecast_rain_6h
        ├── water_coverage
        ├── risk_score
        ├── critical_time
        └── last_safe_departure
```

---

## 7. División de caminos

Los caminos pueden dividirse en segmentos de longitud fija.

Para el MVP se recomienda:

```text
250 m
o
500 m
```

El tamaño debe ser configurable.

La división permite detectar que un tramo específico representa el cuello de botella del recorrido.

Ejemplo:

```text
Camino de 4 km
       ↓
8 segmentos de 500 m
       ↓
cada segmento se evalúa individualmente
```

---

## 8. Fuentes externas

Las fuentes detalladas se documentan en `03_DATOS_Y_GEOESPACIAL.md`.

A nivel de arquitectura, el MVP considera:

### IDECorr

Uso:

- caminos;
- cartografía local;
- geometrías geográficas.

### IGN

Uso:

- Modelo Digital de Elevación;
- elevación;
- pendiente;
- variables topográficas derivadas.

### Copernicus Sentinel-1

Uso:

- observaciones satelitales;
- detección de agua;
- cambios de superficie;
- proximidad de zonas anegadas.

### SMN

Uso:

- pronóstico meteorológico;
- lluvia futura.

### NASA GPM / IMERG

Uso:

- lluvia acumulada reciente;
- lluvia histórica cercana al momento de inferencia.

---

## 9. Tipos de datos

El sistema maneja tres grupos de datos.

### 9.1 Datos estáticos

Cambian poco o casi nunca.

Ejemplos:

```text
geometry
road_type
elevation
slope
flow_accumulation
distance_to_water
```

Se cargan durante la preparación inicial.

### 9.2 Datos dinámicos

Cambian con el tiempo.

Ejemplos:

```text
rain_6h
rain_24h
rain_72h
forecast_rain_3h
forecast_rain_6h
water_coverage
```

Se actualizan periódicamente.

### 9.3 Datos derivados

Son generados por el sistema.

Ejemplos:

```text
risk_score
risk_level
critical_time
last_safe_departure
```

---

## 10. Base de datos

La base recomendada es:

```text
PostgreSQL + PostGIS
```

PostGIS permite almacenar y consultar geometrías geográficas.

---

## 11. Tablas principales

### 11.1 `roads`

Representa caminos completos.

Campos sugeridos:

```text
id
name
geometry
source
created_at
updated_at
```

Tipo geográfico:

```text
LINESTRING / MULTILINESTRING
```

---

### 11.2 `road_segments`

Representa los segmentos utilizados para predicción.

Campos:

```text
id
road_id
segment_index
geometry
length_m
road_type
elevation
slope
flow_accumulation
distance_to_water
created_at
updated_at
```

---

### 11.3 `weather_observations`

Datos meteorológicos observados.

Campos:

```text
id
segment_id
timestamp
rain_1h
rain_6h
rain_24h
rain_72h
source
created_at
```

---

### 11.4 `weather_forecasts`

Pronóstico meteorológico.

Campos:

```text
id
segment_id
generated_at
forecast_time
forecast_rain_1h
forecast_rain_3h
forecast_rain_6h
forecast_rain_12h
source
```

---

### 11.5 `satellite_features`

Features extraídas de imágenes satelitales.

Campos:

```text
id
segment_id
observation_time
water_coverage_50m
water_coverage_100m
water_change
backscatter_mean
source
source_product_id
created_at
```

---

### 11.6 `feature_snapshots`

Representa el vector final usado para inferencia.

Campos:

```text
id
segment_id
generated_at

rain_6h
rain_24h
rain_72h

forecast_rain_3h
forecast_rain_6h
forecast_rain_12h

elevation
slope
flow_accumulation
distance_to_water

water_coverage_50m
water_coverage_100m
water_change

model_feature_version
```

Esta tabla es útil para:

- trazabilidad;
- debugging;
- reproducibilidad;
- reentrenamiento.

---

### 11.7 `risk_predictions`

Resultado del modelo.

Campos:

```text
id
segment_id
generated_at
prediction_time
risk_score
risk_level
model_version
created_at
```

Ejemplo:

```text
segment_id: 152
prediction_time: 2026-09-03 18:00
risk_score: 0.78
risk_level: CRITICAL
```

---

### 11.8 `route_windows`

Resultado de Última Ventana.

Campos:

```text
id
route_id
generated_at
critical_segment_id
critical_time
travel_time_minutes
safety_margin_minutes
last_safe_departure
created_at
```

---

### 11.9 `alerts`

Campos:

```text
id
segment_id
route_id
alert_type
severity
message
generated_at
read_at
```

---

## 12. Relaciones principales

```text
roads
  │
  └── road_segments
          │
          ├── weather_observations
          ├── weather_forecasts
          ├── satellite_features
          ├── feature_snapshots
          ├── risk_predictions
          └── alerts
```

---

## 13. ETL

La capa ETL obtiene datos externos, los transforma y los persiste.

Cada fuente debe tener su propio adapter.

Ejemplo:

```text
src/data_sources/

smn.py
gpm.py
sentinel.py
ign.py
idecorr.py
```

Todos deben retornar estructuras internas consistentes.

Ejemplo conceptual:

```python
class WeatherRecord:
    segment_id: int
    timestamp: datetime
    rainfall: float
```

---

## 14. Pipeline de ingestión

```text
API / Dataset externo
        ↓
Downloader / Client
        ↓
Parsing
        ↓
Validación
        ↓
Transformación de coordenadas
        ↓
Cruce geoespacial
        ↓
Persistencia
```

---

## 15. Pipeline geoespacial

Los datos de distintas fuentes deben relacionarse por coordenadas.

Ejemplo:

```text
Imagen Sentinel
     ↓
georreferenciada
     ↓
buffer alrededor del segmento
     ↓
intersección espacial
     ↓
estadísticas
     ↓
satellite_features
```

El mismo segmento puede utilizarse en el mapa porque conserva su geometría.

---

## 16. CRS

Todos los datos geoespaciales deben normalizarse a sistemas de coordenadas conocidos.

Se recomienda almacenar geometrías operativas en:

```text
EPSG:4326
```

cuando deban exponerse a frontend.

Para cálculos métricos puede utilizarse un CRS proyectado apropiado.

Nunca debe asumirse que dos datasets tienen el mismo CRS sin validarlo.

---

## 17. Feature Pipeline

El sistema debe tener una implementación única para generar features.

Ejemplo:

```text
src/features/
    weather.py
    satellite.py
    topography.py
    build_features.py
```

La misma lógica debe reutilizarse en:

- entrenamiento;
- inferencia.

Esto evita inconsistencias entre el dataset de training y producción.

---

## 18. Contrato de features

El modelo debe recibir siempre el mismo esquema.

Ejemplo inicial:

```text
rain_6h
rain_24h
rain_72h

forecast_rain_3h
forecast_rain_6h
forecast_rain_12h

elevation
slope
flow_accumulation
distance_to_water

water_coverage_50m
water_coverage_100m
water_change
```

El orden, nombre y tipo deben ser versionados.

Ejemplo:

```text
feature_schema_version = v1
```

---

## 19. Modelo ML

El modelo se entrena fuera del backend principal.

Flujo:

```text
Notebooks / scripts
      ↓
Dataset
      ↓
Feature Engineering
      ↓
XGBoost
      ↓
Evaluación
      ↓
Exportación
      ↓
models/model_v1.json
```

El backend carga el modelo en memoria al iniciar.

---

## 20. Servicio de inferencia

Se recomienda implementar:

```text
src/ml/predictor.py
```

Responsabilidad:

1. cargar el modelo;
2. validar features;
3. ejecutar inferencia;
4. devolver `risk_score`.

Contrato conceptual:

```python
predict(features) -> float
```

Ejemplo:

```text
input:
{
    rain_24h: 65,
    rain_72h: 140,
    forecast_rain_6h: 43,
    slope: 0.6,
    water_coverage_100m: 0.28
}

output:
0.81
```

---

## 21. Predicción temporal

Última Ventana requiere múltiples predicciones futuras.

Ejemplo:

```text
14:00 → 0.24
15:00 → 0.31
16:00 → 0.46
17:00 → 0.61
18:00 → 0.74
19:00 → 0.85
```

Para cada hora futura:

1. se toman las features estáticas;
2. se incorporan los valores meteorológicos correspondientes a ese horizonte;
3. se ejecuta el modelo;
4. se persiste la predicción.

---

## 22. Hora crítica

Debe existir un parámetro configurable:

```text
CRITICAL_RISK_THRESHOLD = 0.70
```

El sistema busca:

```text
primer prediction_time
donde
risk_score >= CRITICAL_RISK_THRESHOLD
```

Ejemplo:

```text
18:00 → 0.74
```

Resultado:

```text
critical_time = 18:00
```

---

## 23. Servicio Última Ventana

Se recomienda:

```text
src/services/last_window.py
```

Entrada:

```text
critical_time
travel_time_minutes
safety_margin_minutes
```

Salida:

```text
last_safe_departure
```

Fórmula:

```text
last_safe_departure =
critical_time
- travel_time
- safety_margin
```

Ejemplo:

```text
18:00
- 1h20
- 40 min
=
16:00
```

---

## 24. Ruta completa

La ruta puede incluir varios segmentos.

Ejemplo:

```text
Route 1

segment 101
segment 102
segment 103
segment 104
```

Se debe identificar el segmento más restrictivo.

```text
critical_segment =
segmento cuya hora crítica ocurre primero
```

La Última Ventana de la ruta depende de ese segmento.

---

## 25. Scheduler

El sistema necesita procesos automáticos.

Opciones:

- APScheduler;
- Celery;
- cron externo.

Para el MVP se recomienda:

```text
APScheduler
```

por simplicidad.

---

## 26. Tareas programadas

Ejemplo:

```text
Cada 1 hora:
    consultar pronóstico
```

Si existe lluvia relevante:

```text
actualizar datos
    ↓
generar features
    ↓
ejecutar inferencia
    ↓
calcular Última Ventana
    ↓
persistir
    ↓
generar alertas
```

---

## 27. Trigger meteorológico

No es necesario ejecutar análisis pesado continuamente.

Puede definirse:

```text
RAIN_TRIGGER_THRESHOLD
```

Ejemplo conceptual:

```text
forecast_rain_12h >= 20 mm
```

Cuando se supera:

```text
analysis_required = true
```

El valor es configurable para el MVP.

---

## 28. Backend

El backend se implementará con FastAPI.

Responsabilidades:

- servir API REST;
- acceder a PostGIS;
- ejecutar jobs;
- consumir fuentes externas;
- construir features;
- ejecutar inferencia;
- calcular Última Ventana;
- generar alertas.

---

## 29. Módulos del backend

Estructura sugerida:

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── roads.py
│   │   ├── predictions.py
│   │   ├── routes.py
│   │   └── alerts.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── scheduler.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── models.py
│   │   └── repositories/
│   │
│   ├── data_sources/
│   │   ├── smn.py
│   │   ├── gpm.py
│   │   ├── sentinel.py
│   │   ├── ign.py
│   │   └── idecorr.py
│   │
│   ├── features/
│   │   └── builder.py
│   │
│   ├── ml/
│   │   └── predictor.py
│   │
│   └── services/
│       ├── prediction_service.py
│       ├── risk_service.py
│       ├── last_window.py
│       └── alert_service.py
│
└── tests/
```

---

## 30. Endpoints mínimos

### Caminos

```text
GET /api/roads
GET /api/roads/{road_id}
GET /api/segments/{segment_id}
```

### Predicciones

```text
GET /api/segments/{segment_id}/risk
GET /api/segments/{segment_id}/forecast
```

### Rutas

```text
GET /api/routes/{route_id}
GET /api/routes/{route_id}/last-window
```

### Alertas

```text
GET /api/alerts
```

### Operación manual del MVP

```text
POST /api/predictions/run
```

Este endpoint permite ejecutar una predicción manual durante la demo.

---

## 31. Respuesta API para mapa

Ejemplo:

```json
{
  "segmentId": 152,
  "roadId": 23,
  "riskScore": 0.81,
  "riskLevel": "CRITICAL",
  "criticalTime": "2026-09-03T18:00:00-03:00",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-58.8342, -27.4821],
      [-58.8328, -27.4817]
    ]
  }
}
```

Se recomienda retornar geometrías como GeoJSON.

---

## 32. Frontend

El frontend tiene una responsabilidad principalmente visual.

No calcula el riesgo.

Consume la API y representa:

- caminos;
- colores;
- riesgo;
- Última Ventana;
- alertas.

---

## 33. Mapa

Opciones:

```text
React + Leaflet
```

o:

```text
React + MapLibre
```

Para hackathon, Leaflet es suficiente.

Mapa base:

```text
OpenStreetMap
```

---

## 34. Capas del mapa

### Capa 1

Mapa base.

### Capa 2

Caminos.

### Capa 3

Segmentos coloreados según riesgo.

### Capa 4

Establecimiento / origen.

### Capa 5

Opcional:

zonas de agua detectada.

---

## 35. Colores de riesgo

Ejemplo conceptual:

```text
LOW       → verde
MODERATE  → amarillo
HIGH      → naranja
CRITICAL  → rojo
```

Los colores son responsabilidad del frontend.

La API solo expone:

```text
risk_level
```

---

## 36. Flujo frontend

```text
Usuario abre mapa
        ↓
GET /roads
        ↓
Frontend dibuja caminos
        ↓
GET /risk
        ↓
Colorea segmentos
        ↓
Usuario hace click
        ↓
GET /segment/{id}/forecast
        ↓
Muestra panel de detalle
```

---

## 37. Estado del sistema

El frontend debe mostrar:

```text
Última actualización:
03/09/2026 15:00
```

Esto es importante porque los datos tienen diferentes edades.

---

## 38. Alertas

El backend genera la alerta.

El frontend solamente la muestra.

Regla conceptual:

```text
if risk_level == CRITICAL
or last_safe_departure is near:
    create alert
```

Para el MVP no es obligatorio integrar servicios externos.

---

## 39. Integración satélite ↔ mapa

Las imágenes satelitales no se envían necesariamente al mapa.

Flujo:

```text
Sentinel
    ↓
imagen georreferenciada
    ↓
procesamiento
    ↓
features asociadas a segment_id
    ↓
ML
    ↓
risk_score
    ↓
segment_id
    ↓
geometría guardada
    ↓
frontend pinta ese segmento
```

La relación ocurre mediante:

```text
coordenadas + road_segment_id
```

---

## 40. Modelo de ejecución

### Inicialización

```text
1. Cargar caminos
2. Segmentar caminos
3. Cargar topografía
4. Calcular features estáticas
5. Persistir
```

### Operación

```text
1. Scheduler consulta clima
2. Detecta evento relevante
3. Actualiza datos dinámicos
4. Construye feature snapshots
5. Ejecuta ML
6. Guarda predicciones
7. Calcula Última Ventana
8. Genera alertas
9. API expone resultados
10. Frontend actualiza mapa
```

---

## 41. Entrenamiento vs inferencia

Deben mantenerse separados.

### Entrenamiento

```text
notebooks/
scripts/
dataset histórico/sintético
        ↓
train
        ↓
model_v1.json
```

### Inferencia

```text
backend
    ↓
features actuales
    ↓
model_v1.json
    ↓
risk_score
```

El backend no reentrena automáticamente en el MVP.

---

## 42. Jupyter y Google Colab

Se recomienda usar Jupyter/Colab para:

- exploración;
- limpieza;
- visualización geoespacial;
- construcción de dataset;
- feature engineering experimental;
- entrenamiento;
- evaluación.

No se recomienda usar Colab para:

- backend;
- scheduler;
- API;
- base de datos;
- producción.

---

## 43. Estructura general del repositorio

```text
ultima-ventana/
│
├── backend/
│
├── frontend/
│
├── src/
│   ├── data/
│   ├── geo/
│   ├── features/
│   └── ml/
│
├── notebooks/
│
├── models/
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── database/
│   ├── migrations/
│   └── seed/
│
├── docs/
│   ├── 01_PRODUCTO_Y_FUNCIONALIDAD.md
│   ├── 02_ARQUITECTURA_TECNICA.md
│   ├── 03_DATOS_Y_GEOESPACIAL.md
│   └── 04_MACHINE_LEARNING.md
│
├── docker/
│
├── docker-compose.yml
│
├── .env.example
│
└── README.md
```

---

## 44. Directorio `data`

No deben subirse datasets pesados a Git.

Estructura:

```text
data/raw
data/interim
data/processed
```

Agregar al `.gitignore` cuando corresponda.

---

## 45. Directorio `models`

Ejemplo:

```text
models/
├── model_v1.json
├── feature_schema_v1.json
└── metadata_v1.json
```

`metadata_v1.json` podría incluir:

```json
{
  "model_version": "v1",
  "algorithm": "xgboost",
  "feature_schema": "v1",
  "critical_threshold": 0.70
}
```

---

## 46. Configuración

Variables configurables:

```text
DATABASE_URL
CRITICAL_RISK_THRESHOLD
RAIN_TRIGGER_THRESHOLD
SAFETY_MARGIN_MINUTES
MODEL_PATH
SEGMENT_LENGTH_METERS
```

Además:

```text
API keys
external endpoints
```

No deben hardcodearse secretos.

---

## 47. Docker

Docker Compose puede levantar:

```text
backend
postgres
frontend
```

Ejemplo:

```text
docker-compose up
```

No es necesario contenerizar Colab.

---

## 48. Logging

Registrar:

- inicio y fin de jobs;
- fuentes consultadas;
- errores externos;
- número de segmentos procesados;
- versión del modelo;
- tiempo de inferencia;
- alertas generadas.

Ejemplo:

```text
PredictionJob started
segments=342
model=v1
status=success
duration=12.3s
```

---

## 49. Manejo de fallos

Una fuente externa puede no responder.

Por lo tanto:

```text
API externa falla
      ↓
usar último dato válido
      ↓
registrar antigüedad
      ↓
continuar si es aceptable
```

El MVP debería evitar que una falla no crítica detenga todo el pipeline.

---

## 50. Freshness de datos

Cada observación debe conservar:

```text
timestamp
source
```

Ejemplo:

```text
satellite_feature
observation_time = 2026-09-02 10:30

weather_forecast
generated_at = 2026-09-03 14:00
```

Así el sistema sabe qué tan reciente es cada entrada.

---

## 51. Versionado

Versionar al menos:

```text
model_version
feature_schema_version
```

Ejemplo:

```text
model_v1
features_v1
```

Esto facilita reemplazar el modelo sin romper la API.

---

## 52. Seguridad mínima

Para el MVP:

- secretos en variables de entorno;
- validación de inputs;
- CORS configurado;
- no exponer credenciales;
- evitar endpoints administrativos públicos;
- logs sin secretos;
- consultas parametrizadas mediante ORM.

---

## 53. Testing mínimo

### Unit tests

- cálculo de Última Ventana;
- clasificación de riesgo;
- construcción de features;
- validación del modelo.

### Integration tests

- conexión PostGIS;
- API → DB;
- feature pipeline → modelo.

### Smoke test

```text
POST /predictions/run
        ↓
prediction stored
        ↓
GET /roads/risk
        ↓
response valid
```

---

## 54. Criterios técnicos de aceptación

La arquitectura se considera funcional para el MVP si:

1. PostgreSQL + PostGIS inicia correctamente.
2. Se pueden cargar caminos.
3. Los caminos pueden dividirse en segmentos.
4. Cada segmento mantiene una geometría válida.
5. Se pueden persistir datos meteorológicos.
6. Se pueden persistir features satelitales.
7. Se genera un vector de features consistente.
8. El backend carga el modelo.
9. El modelo genera `risk_score`.
10. Se generan predicciones futuras.
11. Se obtiene `critical_time`.
12. Se calcula `last_safe_departure`.
13. FastAPI expone resultados.
14. React representa segmentos sobre el mapa.
15. Una ejecución completa puede demostrarse de punta a punta.

---

## 55. Prioridad de implementación

### Prioridad 1

```text
PostGIS
caminos
segmentación
mapa
```

Primero debe existir el territorio.

### Prioridad 2

```text
datos meteorológicos
topografía
features
```

### Prioridad 3

```text
modelo
risk_score
```

### Prioridad 4

```text
predicción temporal
Última Ventana
```

### Prioridad 5

```text
alertas
mejoras visuales
```

---

## 56. Estrategia para la demo

Debe existir un modo controlado para ejecutar el sistema.

Por ejemplo:

```text
POST /api/predictions/run
```

La demo no debe depender exclusivamente de que en ese momento exista una tormenta real.

Se puede utilizar:

- un escenario histórico;
- un escenario de prueba;
- datos precargados;
- un pronóstico simulado.

Pero el pipeline debe ser el mismo que utilizaría información real.

---

## 57. Arquitectura mínima viable

Si el tiempo de hackathon es limitado, la versión mínima puede reducirse a:

```text
IDECorr / GeoJSON de caminos
        ↓
PostGIS
        ↓
features precalculadas
        ↓
modelo XGBoost
        ↓
FastAPI
        ↓
React + Leaflet
```

Las integraciones automáticas pueden implementarse progresivamente.

---

## 58. Arquitectura objetivo del MVP

La versión deseada es:

```text
SMN ───────────────────┐
NASA GPM ───────────────┤
Sentinel-1 ─────────────┤
IGN ────────────────────┤
IDECorr ────────────────┘
          ↓
       ETL / GIS
          ↓
 PostgreSQL + PostGIS
          ↓
 Feature Engineering
          ↓
      XGBoost
          ↓
predicción por hora
          ↓
  hora crítica
          ↓
Última Ventana
          ↓
      FastAPI
          ↓
React + Leaflet
          ↓
 mapa + alertas
```

---

## 59. Separación de responsabilidades

### Equipo Data / GIS

Responsable de:

- fuentes;
- reproyección;
- segmentación;
- extracción de features;
- dataset.

### Equipo ML

Responsable de:

- dataset final;
- entrenamiento;
- modelo;
- inferencia;
- documentación de features.

### Equipo Backend

Responsable de:

- DB;
- API;
- scheduler;
- integración;
- cálculo de Última Ventana;
- persistencia.

### Equipo Frontend

Responsable de:

- mapa;
- visualización;
- paneles;
- alertas;
- UX.

---

## 60. Regla fundamental de integración

Todos los componentes deben compartir la misma entidad:

```text
road_segment_id
```

Nunca se debe depender de nombres de caminos para unir información.

Ejemplo correcto:

```text
segment_id = 152
```

Ejemplo incorrecto:

```text
"Camino Paso Martínez km más o menos 4"
```

---

## 61. Resumen técnico

Última Ventana se implementará como una plataforma geoespacial compuesta por:

```text
datos externos
+
ETL
+
PostGIS
+
feature engineering
+
ML
+
motor temporal
+
API
+
mapa
```

La arquitectura debe priorizar tres propiedades:

1. **Trazabilidad:** saber de dónde salió cada predicción.
2. **Reutilización:** mismo feature pipeline en training e inference.
3. **Simplicidad:** suficientes componentes para demostrar valor sin convertir el hackathon en un sistema productivo sobredimensionado.

---

## 62. Decisión arquitectónica principal

El backend no debe intentar “interpretar imágenes satelitales” directamente durante cada request del usuario.

La arquitectura correcta es:

```text
fuente satelital
     ↓
procesamiento batch / ETL
     ↓
features
     ↓
PostGIS
     ↓
modelo
```

Y posteriormente:

```text
frontend
     ↓
API
     ↓
predicciones ya procesadas
```

Esto mantiene baja la latencia y simplifica la demo.

---

## 63. Resultado esperado

Al finalizar la implementación del MVP debe ser posible ejecutar:

```text
Pronóstico de lluvia
        ↓
actualización de features
        ↓
modelo
        ↓
risk score por segmento
        ↓
hora crítica
        ↓
Última Ventana
        ↓
mapa
        ↓
alerta
```

y demostrar al jurado que un evento meteorológico puede convertirse en una recomendación logística concreta.

