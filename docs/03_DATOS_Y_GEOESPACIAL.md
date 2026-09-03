# Última Ventana — Datos y Geoespacial

## 1. Objetivo del documento

Este documento define cómo se obtienen, normalizan, procesan, relacionan y persisten los datos geoespaciales utilizados por el MVP de **Última Ventana**.

La finalidad es que el equipo pueda responder con precisión:

- qué fuentes externas se utilizarán;
- qué dato aporta cada fuente;
- qué información se descarga una sola vez y cuál se actualiza;
- cómo se relacionan imágenes satelitales, caminos, topografía y meteorología;
- cómo se transforman datos geográficos en features utilizables por Machine Learning;
- qué información debe persistirse;
- cómo mantener una referencia espacial consistente;
- qué simplificaciones son aceptables durante el hackathon.

Este documento no define el algoritmo de Machine Learning en profundidad. Esa responsabilidad corresponde a `04_MACHINE_LEARNING.md`.

---

# 2. Principio fundamental

Todos los datos del sistema deben terminar relacionados con una misma unidad geográfica:

```text
road_segment_id
```

Un `road_segment` representa un tramo de camino rural.

Ejemplo:

```text
road_segment_id = 152
geometry = LINESTRING(...)
```

A ese segmento se le asocian:

```text
topografía
meteorología
lluvia antecedente
información satelital
features derivadas
predicciones
```

Por lo tanto:

```text
                    road_segment_id
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       camino          topografía        satélite
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                     meteorología
                           │
                           ▼
                  feature engineering
                           │
                           ▼
                         ML
```

La unión entre fuentes no se realiza por nombre del lugar.

Se realiza mediante:

```text
coordenadas
+
geometrías
+
operaciones espaciales
+
road_segment_id
```

---

# 3. Fuentes seleccionadas para el MVP

Para mantener el proyecto realizable durante el hackathon se utilizarán cinco fuentes principales.

| Fuente | Uso principal |
|---|---|
| IDECorr | geometría de caminos rurales y cartografía provincial |
| IGN MDE-Ar | elevación y topografía |
| Copernicus Sentinel-1 | estado reciente del terreno y detección de agua |
| NASA GPM / IMERG | precipitación antecedente |
| SMN | pronóstico de lluvia futura |

No se incorporarán nuevas fuentes al MVP salvo que una de estas resulte técnicamente inaccesible.

---

# 4. Regla de simplificación del MVP

El sistema debe priorizar:

```text
pocas fuentes
+
pipeline reproducible
+
datos georreferenciados
+
demo funcional
```

antes que:

```text
muchas fuentes
+
integraciones incompletas
+
datos duplicados
+
pipeline difícil de reproducir
```

Fuentes como:

- Sentinel-2;
- NASA SMAP;
- SoilGrids;
- INA;
- ICAA;
- sensores IoT;
- estaciones privadas;

pueden incorporarse posteriormente.

---

# 5. Fuente 1 — IDECorr

## 5.1 Función

IDECorr será la fuente preferida para obtener la cartografía vectorial de Corrientes.

El sistema necesita especialmente:

- caminos;
- rutas;
- cursos de agua, si están disponibles;
- cuerpos de agua, si están disponibles;
- otras capas territoriales útiles para contextualización.

IDECorr publica geoservicios interoperables, incluyendo WMS y WFS.

Para análisis se debe preferir **WFS** cuando la capa requerida esté disponible, porque permite obtener entidades vectoriales y no únicamente una imagen del mapa.

Fuente oficial:

https://ide.corrientes.gob.ar/articulo/geoservicios

---

## 5.2 Qué necesitamos obtener

Como mínimo:

```text
road_id
road_name
geometry
source
```

La geometría debe terminar representada como:

```text
LINESTRING
```

o:

```text
MULTILINESTRING
```

---

## 5.3 Alternativa

Si IDECorr no posee cobertura suficiente de caminos rurales en la región elegida para la demo, se podrá utilizar OpenStreetMap como fuente auxiliar.

Sin embargo, para el MVP se intentará primero trabajar con información provincial.

---

# 6. Fuente 2 — IGN MDE-Ar

## 6.1 Función

El Instituto Geográfico Nacional proporciona el Modelo Digital de Elevaciones de Argentina.

Para el MVP se utilizará:

**MDE-Ar v2.1**

El producto cubre el territorio continental argentino y posee resolución espacial aproximada de 30 metros.

Fuente oficial:

https://www.ign.gob.ar/content/nuevo-modelo-digital-de-elevaciones-de-la-rep%25C3%25BAblica-argentina

Documentación:

https://www.ign.gob.ar/NuestrasActividades/Geodesia/ModeloDigitalElevaciones/Documentacion

---

## 6.2 Qué representa un MDE

Un Modelo Digital de Elevaciones es un raster donde cada celda contiene un valor de elevación.

Conceptualmente:

```text
Raster

42.3 | 42.1 | 41.8
------------------
42.5 | 41.9 | 41.2
------------------
43.0 | 42.2 | 40.7
```

Cada celda corresponde a una posición real del territorio.

---

## 6.3 Features que se pueden obtener

Para el MVP se priorizarán:

```text
elevation_mean
slope_mean
```

Si el tiempo de desarrollo lo permite:

```text
flow_accumulation
relative_elevation
local_depression
```

No es obligatorio implementar todas las variables hidrológicas derivadas para la primera demo.

---

## 6.4 Procesamiento

Flujo:

```text
MDE-Ar
   ↓
recorte a región del MVP
   ↓
reproyección si corresponde
   ↓
intersección con buffers de caminos
   ↓
estadísticas zonales
   ↓
features topográficas
```

Ejemplo:

```text
road_segment_id = 152

elevation_mean = 51.8
slope_mean = 0.72
```

---

# 7. Fuente 3 — Copernicus Sentinel-1

## 7.1 Función

Sentinel-1 será la principal fuente satelital del MVP.

Se accede mediante:

**Copernicus Data Space Ecosystem**

https://dataspace.copernicus.eu/

Documentación Sentinel-1:

https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel1.html

---

## 7.2 Por qué Sentinel-1

Sentinel-1 utiliza radar de apertura sintética:

```text
SAR
```

Esto es particularmente útil para el proyecto porque puede adquirir información:

- durante el día;
- durante la noche;
- con presencia de nubes;
- durante condiciones meteorológicas adversas.

Esto es preferible para monitoreo de inundaciones frente a depender exclusivamente de imágenes ópticas.

---

# 8. Sentinel-1 no es una fotografía tradicional

Sentinel-1 no debe entenderse como:

```text
JPG
→ mirar
→ clasificar visualmente
```

El producto contiene información radar georreferenciada.

Cada píxel tiene:

```text
posición geográfica
+
valor de señal radar
```

El objetivo es convertir esa información en variables numéricas asociadas a los caminos.

---

# 9. Producto Sentinel-1 recomendado

Para el MVP se recomienda comenzar con productos:

```text
GRD
Ground Range Detected
```

y trabajar con polarizaciones disponibles como:

```text
VV
VH
```

No es necesario implementar procesamiento SAR avanzado completo durante el hackathon.

La prioridad es obtener un pipeline reproducible que permita generar un indicador de presencia/cobertura de agua alrededor de segmentos.

---

# 10. Features satelitales del MVP

Como se utilizará Sentinel-1 y no Sentinel-2, el MVP **no debe depender de NDWI**.

NDWI es una feature típica de imágenes ópticas multiespectrales y puede incorporarse posteriormente mediante Sentinel-2.

Para Sentinel-1 se priorizan features como:

```text
vv_backscatter_mean
vh_backscatter_mean
water_coverage_50m
water_coverage_100m
water_change
```

La implementación exacta dependerá del procesamiento seleccionado.

---

# 11. Water coverage

El sistema puede generar una máscara estimada de agua a partir del raster procesado.

Conceptualmente:

```text
0 = no agua
1 = agua
```

Luego se calcula qué proporción del entorno de un camino está cubierta por agua.

Ejemplo:

```text
buffer = 100 m

total pixels = 500
water pixels = 120

water_coverage_100m = 120 / 500
                    = 0.24
```

Resultado:

```text
water_coverage_100m = 24 %
```

---

# 12. Por qué utilizar buffers

Un camino rural puede tener un ancho mucho menor que la resolución efectiva de un producto satelital.

No conviene preguntar solamente:

> ¿Qué valor tiene exactamente el píxel situado sobre el centro del camino?

Se analiza el entorno.

Ejemplo:

```text
            ┌─────────────────────┐
            │    buffer 100 m     │
────────────┼═════════════════════┼──────────── camino
            │                     │
            └─────────────────────┘
```

Para el MVP se pueden usar dos buffers:

```text
50 m
100 m
```

Y obtener:

```text
water_coverage_50m
water_coverage_100m
```

---

# 13. Cambio temporal de agua

Una feature especialmente útil es medir si la cobertura de agua está creciendo.

Ejemplo:

```text
observación anterior:
water_coverage_100m = 0.12

observación actual:
water_coverage_100m = 0.31
```

Entonces:

```text
water_change = 0.31 - 0.12
             = +0.19
```

Esto representa expansión reciente de agua alrededor del segmento.

---

# 14. Importante: Sentinel no se actualiza cada hora

El backend puede consultar pronósticos meteorológicos cada hora.

Eso no significa que exista una nueva observación Sentinel-1 cada hora.

Por lo tanto, durante inferencia se utilizará:

```text
última observación satelital válida
+
meteorología actual
+
pronóstico futuro
+
topografía
```

El timestamp de la observación satelital debe conservarse siempre.

Ejemplo:

```text
satellite_observation_time =
2026-09-02T09:40:00Z
```

---

# 15. Fuente 4 — NASA GPM / IMERG

## 15.1 Función

NASA GPM / IMERG se utilizará para representar la lluvia antecedente.

El objetivo es responder:

> ¿Cuánta precipitación recibió recientemente la región antes del pronóstico que estamos analizando?

Producto recomendado:

```text
GPM IMERG
```

La familia IMERG ofrece precipitación con cobertura global y resolución temporal de 30 minutos.

Para el MVP interesa principalmente agregar esos datos temporalmente.

Fuente:

https://earthdata.nasa.gov/

Producto IMERG:

https://gis.earthdata.nasa.gov/portal/home/item.html?id=598df0e6fd674ab7855f448f7f6f0e39

---

## 15.2 Resolución

IMERG tiene una resolución espacial aproximada de:

```text
0.1° × 0.1°
```

Por eso debe interpretarse como contexto pluviométrico regional.

No debe afirmarse:

> este segmento de 250 m recibió exactamente X milímetros.

La interpretación correcta es:

> la celda pluviométrica que contiene o rodea este segmento registró aproximadamente X milímetros.

---

# 16. Features derivadas de GPM

Se priorizarán:

```text
rain_6h
rain_24h
rain_72h
```

Opcional:

```text
rain_7d
```

Ejemplo:

```text
road_segment_id = 152

rain_6h  = 13.7 mm
rain_24h = 48.2 mm
rain_72h = 119.4 mm
```

---

# 17. Acumulación temporal

IMERG ofrece intervalos temporales menores que los utilizados por el modelo.

Por lo tanto:

```text
IMERG 30 min
     ↓
agregación temporal
     ↓
6 h
24 h
72 h
```

Ejemplo conceptual:

```python
rain_24h = sum(last_48_half_hour_values)
```

---

# 18. Fuente 5 — SMN

## 18.1 Función

El Servicio Meteorológico Nacional será la fuente meteorológica principal para representar lluvia futura.

El sistema necesita especialmente:

```text
forecast_rain_3h
forecast_rain_6h
forecast_rain_12h
```

La información del SMN debe utilizarse para anticipar cómo evolucionará el riesgo.

Fuentes oficiales:

https://www.smn.gob.ar/

Información sobre datos abiertos:

https://www.argentina.gob.ar/node/178357

El SMN también publica datos de pronóstico numérico mediante conjuntos abiertos asociados al modelo WRF-SMN.

Referencia:

https://www.argentina.gob.ar/noticias/el-smn-disponibiliza-los-pronosticos-numericos-3-dias-traves-de-la-nube-de-servicios-de-aws

---

# 19. Advertencia sobre la integración SMN

Durante la implementación se debe verificar el mecanismo actual de acceso programático al producto meteorológico seleccionado.

No debe desarrollarse el MVP dependiendo de:

- scraping de HTML;
- endpoints privados descubiertos desde el navegador;
- APIs no documentadas;
- URLs temporales.

Si el producto seleccionado se distribuye como archivos meteorológicos y no como REST JSON, se desarrollará un adapter específico.

La arquitectura debe ocultar esta diferencia detrás de:

```text
WeatherProvider
```

---

# 20. Qué dato aporta cada fuente

La combinación definitiva queda:

```text
IDECorr
    ↓
¿Dónde están los caminos?

IGN
    ↓
¿Cómo es la topografía alrededor del camino?

Sentinel-1
    ↓
¿Qué estado reciente presenta el agua alrededor del camino?

NASA GPM
    ↓
¿Cuánto llovió recientemente?

SMN
    ↓
¿Cuánto se espera que llueva?
```

Estas cinco preguntas generan la entrada territorial del modelo.

---

# 21. Flujo geoespacial completo

```text
                     IDECorr
                        │
                        ▼
                 Caminos vectoriales
                        │
                        ▼
                División en segmentos
                        │
                        ▼
                 road_segment_id
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
      IGN            Sentinel-1        GPM
       │                │                │
 elevación         agua cercana      lluvia previa
 pendiente         backscatter       acumulaciones
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
                       SMN
                        │
                 lluvia futura
                        │
                        ▼
                FEATURE SNAPSHOT
```

---

# 22. Definición de región del MVP

No se procesará toda la provincia durante el hackathon.

Se seleccionará una región rural concreta de Corrientes.

El área de interés se representará como:

```text
AOI
Area Of Interest
```

Por ejemplo:

```text
Polygon
```

Todos los datasets se recortarán a esa AOI.

---

# 23. Por qué definir una AOI

Esto reduce:

- tiempo de descarga;
- memoria;
- procesamiento raster;
- número de caminos;
- número de segmentos;
- complejidad de la demo.

Pipeline:

```text
dataset nacional/global
        ↓
clip AOI Corrientes
        ↓
dataset pequeño
        ↓
procesamiento
```

---

# 24. Sistema de coordenadas

Diferentes fuentes pueden usar diferentes CRS.

Ejemplos:

```text
EPSG:4326
UTM
CRS específico del raster
```

No se deben cruzar geometrías sin verificar previamente el CRS.

---

# 25. CRS de almacenamiento y visualización

Para intercambio con frontend se recomienda:

```text
EPSG:4326
```

porque GeoJSON y mapas web trabajan cómodamente con longitud y latitud.

Ejemplo:

```text
longitude = -58.8342
latitude  = -27.4821
```

---

# 26. CRS para cálculos métricos

Operaciones como:

```text
buffer 50 m
buffer 100 m
longitud
distancia
área
```

no deberían calcularse directamente en grados.

Se debe reproyectar temporalmente a un CRS métrico apropiado para Corrientes.

Flujo:

```text
EPSG:4326
    ↓
CRS proyectado métrico
    ↓
buffer / distancia / área
    ↓
resultado
    ↓
EPSG:4326 si hace falta exponerlo
```

---

# 27. Georreferenciación satelital

El raster Sentinel posee información espacial.

Conceptualmente:

```text
pixel [120, 830]
       ↓
coordenada real
       ↓
zona de Corrientes
```

Por lo tanto, el modelo no necesita “aprender dónde está el lugar”.

La posición ya está definida por la georreferenciación.

---

# 28. Relación Sentinel ↔ mapa web

El flujo correcto es:

```text
Sentinel-1
     ↓
raster georreferenciado
     ↓
cruce con road_segment
     ↓
feature
     ↓
risk_score
     ↓
road_segment_id
     ↓
geometry
     ↓
Leaflet / MapLibre
```

El mapa no necesita consumir la imagen Sentinel para conocer dónde colocar la predicción.

---

# 29. Segmentación de caminos

Una vez obtenidos los caminos, se transforman en segmentos.

Para el MVP:

```text
SEGMENT_LENGTH_METERS = 500
```

puede ser un buen punto de partida.

Debe ser configurable.

---

# 30. Ejemplo

Camino:

```text
longitud = 3.8 km
```

Resultado:

```text
segment 1 = 0 - 500 m
segment 2 = 500 - 1000 m
segment 3 = 1000 - 1500 m
...
segment 8 = tramo restante
```

Cada segmento recibe:

```text
id
road_id
segment_index
geometry
length_m
```

---

# 31. Buffer de segmento

Por cada segmento se crean geometrías auxiliares para extracción de contexto.

Ejemplo:

```text
segment geometry
     ↓
buffer 50 m
buffer 100 m
```

Estas geometrías pueden utilizarse para:

- estadísticas raster;
- cobertura de agua;
- elevación media;
- proximidad;
- análisis territorial.

No es obligatorio persistir todos los buffers si pueden regenerarse.

---

# 32. Estadísticas zonales

Cuando un raster se superpone con un buffer, pueden calcularse estadísticas.

Ejemplo topográfico:

```text
elevation_mean
elevation_min
elevation_max
```

Ejemplo Sentinel:

```text
vv_mean
vh_mean
water_fraction
```

Estas operaciones se conocen generalmente como:

```text
zonal statistics
```

---

# 33. Qué persistir y qué no

No todo dato descargado debe almacenarse permanentemente en PostgreSQL.

---

## 33.1 Persistir en PostGIS

Se recomienda persistir:

```text
roads
road_segments

elevation_mean
slope_mean

weather observations
weather forecasts

satellite features

feature snapshots

risk predictions
```

---

## 33.2 Archivos raster

Los GeoTIFF u otros archivos pesados pueden almacenarse en:

```text
data/raw/
data/interim/
```

durante desarrollo.

No es necesario guardar el raster completo dentro de PostgreSQL para el MVP.

---

# 34. Referencia al archivo fuente

Aunque se extraigan features, se debe conservar trazabilidad.

Ejemplo:

```text
source = "sentinel-1"
source_product_id = "..."
observation_time = "..."
```

Esto permite reproducir posteriormente una feature.

---

# 35. Estructura de archivos

```text
data/
│
├── raw/
│   ├── roads/
│   ├── dem/
│   ├── sentinel/
│   ├── gpm/
│   └── smn/
│
├── interim/
│   ├── clipped_dem/
│   ├── processed_sentinel/
│   └── segmented_roads/
│
└── processed/
    ├── static_features.parquet
    ├── dynamic_features.parquet
    └── training_dataset.parquet
```

Los archivos pesados no deben subirse normalmente al repositorio Git.

---

# 36. Tablas geoespaciales mínimas

## `roads`

```text
id
name
geometry
source
```

---

## `road_segments`

```text
id
road_id
segment_index
geometry
length_m

elevation_mean
slope_mean

created_at
updated_at
```

---

## `satellite_features`

```text
id
segment_id
observation_time

vv_backscatter_mean
vh_backscatter_mean

water_coverage_50m
water_coverage_100m
water_change

source
source_product_id
created_at
```

---

## `weather_observations`

```text
id
segment_id
timestamp

rain_6h
rain_24h
rain_72h

source
created_at
```

---

## `weather_forecasts`

```text
id
segment_id
generated_at
forecast_time

forecast_rain_3h
forecast_rain_6h
forecast_rain_12h

source
```

---

# 37. Static features

Se calculan principalmente durante preparación del dataset.

```text
segment_id
elevation_mean
slope_mean
```

Opcionales:

```text
flow_accumulation
distance_to_water
road_type
```

No deben recalcularse en cada predicción.

---

# 38. Dynamic features

Se actualizan con el tiempo.

```text
rain_6h
rain_24h
rain_72h

forecast_rain_3h
forecast_rain_6h
forecast_rain_12h

vv_backscatter_mean
vh_backscatter_mean

water_coverage_50m
water_coverage_100m
water_change
```

---

# 39. Feature snapshot

Antes de ejecutar el modelo se construye una observación completa.

Ejemplo:

```text
segment_id = 152
prediction_time = 18:00

elevation_mean = 51.8
slope_mean = 0.72

rain_6h = 14.1
rain_24h = 48.3
rain_72h = 118.9

forecast_rain_3h = 22.4
forecast_rain_6h = 39.2
forecast_rain_12h = 67.5

water_coverage_50m = 0.18
water_coverage_100m = 0.26
water_change = 0.09
```

Este registro es el que posteriormente consume el modelo.

---

# 40. Pipeline inicial de caminos

```text
IDECorr
   ↓
descargar / consultar capa
   ↓
GeoDataFrame
   ↓
clip AOI
   ↓
validar geometrías
   ↓
reproyectar
   ↓
segmentar
   ↓
PostGIS
```

---

# 41. Pipeline inicial topográfico

```text
IGN MDE-Ar
     ↓
descargar hoja correspondiente
     ↓
clip AOI
     ↓
CRS correcto
     ↓
calcular slope
     ↓
zonal statistics
     ↓
road_segments
```

---

# 42. Pipeline Sentinel-1

Versión conceptual:

```text
Copernicus Data Space
        ↓
buscar escena por:
AOI + fecha
        ↓
obtener producto Sentinel-1
        ↓
preprocesar
        ↓
normalizar geometría / CRS
        ↓
generar representación de agua
        ↓
intersectar buffers
        ↓
calcular estadísticas
        ↓
satellite_features
```

---

# 43. Preprocesamiento Sentinel-1

El procesamiento SAR real puede involucrar varias etapas técnicas.

Durante el hackathon debe priorizarse una implementación ya soportada por herramientas existentes.

Según la forma de acceso seleccionada, pueden aparecer pasos como:

```text
orbit correction
radiometric calibration
speckle filtering
terrain correction
backscatter conversion
```

No conviene implementar estos algoritmos manualmente.

Se deben utilizar herramientas/librerías/servicios existentes.

---

# 44. Estrategia Sentinel para el hackathon

Prioridad:

> obtener una feature consistente y georreferenciada.

No prioridad:

> construir un pipeline científico SAR completo desde cero.

Si el acceso a productos procesados simplifica considerablemente el trabajo, se debe preferir esa opción.

---

# 45. Pipeline NASA GPM

```text
NASA GPM / IMERG
       ↓
seleccionar AOI
       ↓
seleccionar período
       ↓
obtener precipitación
       ↓
normalizar timestamp
       ↓
agregar:
6 h
24 h
72 h
       ↓
asociar a segmentos
       ↓
weather_observations
```

---

# 46. Asociación de GPM a segmentos

Debido a la resolución de IMERG, muchos segmentos compartirán la misma celda meteorológica.

Esto es correcto.

Ejemplo:

```text
IMERG cell 1038
    │
    ├── segment 151
    ├── segment 152
    ├── segment 153
    └── segment 154
```

No debe inventarse mayor resolución de la que realmente posee el producto.

---

# 47. Pipeline SMN

Conceptualmente:

```text
SMN
 ↓
pronóstico disponible
 ↓
seleccionar zona / grilla
 ↓
normalizar horario
 ↓
acumular precipitación futura
 ↓
3 h
6 h
12 h
 ↓
asociar a segmentos
 ↓
weather_forecasts
```

---

# 48. Tiempo y zona horaria

Todas las fuentes pueden manejar timestamps diferentes.

La base debe almacenar tiempos de forma consistente.

Recomendación:

```text
UTC en persistencia
```

y convertir a:

```text
America/Argentina/Cordoba
```

o zona local correspondiente en interfaz.

No se deben mezclar tiempos locales sin offset y UTC.

---

# 49. Freshness

Cada dato dinámico debe contener:

```text
observation_time
o
generated_at
```

Ejemplo:

```text
GPM:
observation_time = 12:00 UTC

Sentinel:
observation_time = día anterior

SMN:
generated_at = 13:00 UTC
```

El modelo puede usar datos de distintas edades, pero esa diferencia debe ser explícita.

---

# 50. Validaciones de ingesta

Antes de persistir:

### Geometría

```text
geometry != null
geometry.is_valid
```

### Raster

```text
CRS disponible
transform disponible
nodata identificado
```

### Meteorología

```text
rain >= 0
timestamp válido
source != null
```

### Satellite features

```text
0 <= water_coverage <= 1
```

---

# 51. Manejo de valores faltantes

Una observación satelital puede no estar disponible para el momento exacto.

No se debe generar un valor falso.

Se debe:

```text
usar última observación válida
+
guardar su timestamp
```

o:

```text
marcar feature como null
```

La estrategia final de imputación corresponde al pipeline de ML.

---

# 52. Relación entre resolución y precisión

Las fuentes tienen escalas diferentes.

Ejemplo conceptual:

```text
camino segmentado:     500 m
IGN:                   ~30 m
Sentinel-1:            decenas de metros según producto/proceso
GPM IMERG:             ~0.1°
```

Por lo tanto:

> una predicción por segmento no significa que todas las variables tengan resolución de 500 m.

El sistema combina señales con diferentes escalas espaciales.

Esto debe explicarse claramente durante el pitch si surge la pregunta.

---

# 53. Lo que NO debe afirmar el MVP

No decir:

> “Sabemos exactamente cuántos milímetros cayeron sobre estos 250 metros.”

si el dato proviene de una celda IMERG mucho mayor.

No decir:

> “Sentinel confirma que el camino está cortado.”

si solamente se detectó agua alrededor.

No decir:

> “El modelo conoce cada centímetro del terreno.”

La salida es una estimación de riesgo.

---

# 54. Dataset para entrenamiento

Una vez procesadas las fuentes, el dataset final tendrá una estructura tabular.

Ejemplo:

```text
segment_id
timestamp

elevation_mean
slope_mean

rain_6h
rain_24h
rain_72h

forecast_rain_3h
forecast_rain_6h
forecast_rain_12h

vv_backscatter_mean
vh_backscatter_mean
water_coverage_50m
water_coverage_100m
water_change

target
```

El tratamiento del `target` se define en `04_MACHINE_LEARNING.md`.

---

# 55. Datos históricos y datos de inferencia

Deben utilizar el mismo esquema conceptual.

## Entrenamiento

```text
datos históricos
+
features históricas
+
target
```

## Inferencia

```text
últimos datos disponibles
+
pronóstico futuro
```

Las features deben mantener:

```text
mismos nombres
mismos tipos
mismas unidades
misma lógica de cálculo
```

---

# 56. Unidades

Congelar unidades desde el comienzo.

### Precipitación

```text
mm
```

### Distancias

```text
m
```

### Elevación

```text
m
```

### Pendiente

Elegir una representación y mantenerla:

```text
porcentaje
```

o:

```text
grados
```

Para el MVP se recomienda:

```text
slope_percent
```

### Cobertura de agua

```text
0.0 a 1.0
```

---

# 57. Nombres de features

Evitar nombres ambiguos.

Incorrecto:

```text
rain
water
height
```

Preferido:

```text
rain_24h_mm
forecast_rain_6h_mm
elevation_mean_m
slope_mean_pct
water_coverage_100m_ratio
```

Esto reduce errores durante integración.

---

# 58. Convención propuesta

Features iniciales:

```text
rain_6h_mm
rain_24h_mm
rain_72h_mm

forecast_rain_3h_mm
forecast_rain_6h_mm
forecast_rain_12h_mm

elevation_mean_m
slope_mean_pct

vv_backscatter_mean
vh_backscatter_mean

water_coverage_50m_ratio
water_coverage_100m_ratio
water_change_ratio
```

---

# 59. Feature set mínimo obligatorio

Si el tiempo se vuelve crítico, el sistema debe funcionar al menos con:

```text
rain_24h_mm
rain_72h_mm

forecast_rain_6h_mm
forecast_rain_12h_mm

elevation_mean_m
slope_mean_pct

water_coverage_100m_ratio
```

Con esto ya existe:

```text
lluvia pasada
+
lluvia futura
+
topografía
+
estado superficial
```

---

# 60. Features opcionales

Solo agregar si el pipeline principal ya funciona:

```text
flow_accumulation
distance_to_water
road_type
water_change
vv_backscatter_mean
vh_backscatter_mean
rain_7d
```

---

# 61. No introducir Sentinel-2 en el camino crítico del MVP

Sentinel-2 permitiría calcular índices como:

```text
NDWI
NDVI
```

pero introduce:

- otra fuente;
- bandas ópticas;
- problemas de nubosidad;
- procesamiento adicional.

Por lo tanto:

> Sentinel-2 se considera mejora futura.

El modelo del MVP debe poder funcionar sin NDWI.

---

# 62. Procesamiento local vs Colab

## Local / backend

Apropiado para:

```text
ETL pequeño
PostGIS
GeoJSON
segmentación
consultas
persistencia
```

## Jupyter / Google Colab

Apropiado para:

```text
exploración raster
GeoPandas
Rasterio
visualización
pruebas de Sentinel
generación del dataset
feature engineering experimental
```

Una vez estabilizada una función, debe migrarse del notebook a código reutilizable en:

```text
src/
```

---

# 63. Notebooks geoespaciales sugeridos

```text
notebooks/

00_aoi_y_caminos.ipynb
01_topografia_ign.ipynb
02_sentinel1.ipynb
03_gpm.ipynb
04_weather_forecast.ipynb
05_build_dataset.ipynb
```

Los notebooks son herramientas de exploración y construcción.

No deben convertirse en el backend productivo.

---

# 64. Módulos Python sugeridos

```text
src/
├── data/
│   ├── idecorr.py
│   ├── ign.py
│   ├── sentinel.py
│   ├── gpm.py
│   └── smn.py
│
├── geo/
│   ├── crs.py
│   ├── segmentation.py
│   ├── buffers.py
│   ├── raster.py
│   └── zonal_stats.py
│
└── features/
    ├── static.py
    ├── satellite.py
    ├── weather.py
    └── builder.py
```

---

# 65. Proceso inicial recomendado

Orden de implementación:

### Paso 1

Definir AOI.

### Paso 2

Obtener caminos IDECorr.

### Paso 3

Segmentarlos.

### Paso 4

Mostrar segmentos en un mapa.

### Paso 5

Agregar elevación y pendiente.

### Paso 6

Procesar una escena Sentinel-1.

### Paso 7

Extraer `water_coverage`.

### Paso 8

Obtener GPM.

### Paso 9

Generar acumulaciones de lluvia.

### Paso 10

Integrar pronóstico.

### Paso 11

Construir el primer `feature_snapshot`.

Solo después de esto conviene cerrar el entrenamiento ML.

---

# 66. Primer hito geoespacial

Antes de entrenar cualquier modelo debería ser posible consultar:

```text
road_segment_id = 152
```

y obtener:

```text
geometry
elevation_mean_m
slope_mean_pct

rain_24h_mm
rain_72h_mm

forecast_rain_6h_mm
forecast_rain_12h_mm

water_coverage_100m_ratio
```

Si eso funciona, la capa de datos está preparada para ML.

---

# 67. Ejemplo end-to-end

Supongamos:

```text
segment_id = 152
```

### IDECorr

```text
geometry = tramo rural de 500 m
```

### IGN

```text
elevation_mean_m = 48.7
slope_mean_pct = 0.42
```

### Sentinel-1

```text
water_coverage_100m_ratio = 0.27
```

### NASA GPM

```text
rain_24h_mm = 61.4
rain_72h_mm = 138.2
```

### SMN

```text
forecast_rain_6h_mm = 34.0
forecast_rain_12h_mm = 62.0
```

Resultado:

```text
FEATURE SNAPSHOT

segment_id = 152

elevation_mean_m = 48.7
slope_mean_pct = 0.42

water_coverage_100m_ratio = 0.27

rain_24h_mm = 61.4
rain_72h_mm = 138.2

forecast_rain_6h_mm = 34.0
forecast_rain_12h_mm = 62.0
```

Este vector pasa posteriormente al modelo.

---

# 68. Datos reales vs datos sintéticos

Los datos geoespaciales y meteorológicos del MVP deben ser reales siempre que sea posible.

Ejemplos:

```text
caminos → reales
topografía → real
Sentinel → real
GPM → real
pronóstico → real o escenario controlado de demo
```

Los datos sintéticos se reservarán principalmente para resolver limitaciones del dataset supervisado de entrenamiento.

No se deben reemplazar innecesariamente fuentes geográficas reales por valores aleatorios.

---

# 69. Escenario controlado de demo

La demo no debe depender de que el día del hackathon exista lluvia intensa.

Por eso debe poder cargarse un escenario reproducible:

```text
fecha histórica
o
pronóstico simulado
```

sobre caminos y topografía reales.

Esto permite mostrar:

```text
condiciones iniciales
        ↓
incremento de lluvia
        ↓
incremento del riesgo
        ↓
Última Ventana
```

---

# 70. Reproducibilidad

Cada pipeline debería poder ejecutarse con:

```text
AOI
fecha inicial
fecha final
```

Ejemplo:

```text
python build_dataset.py \
  --aoi corrientes_demo.geojson \
  --start 2026-01-01 \
  --end 2026-08-31
```

La sintaxis exacta se definirá durante implementación.

---

# 71. Cache

Las fuentes geoespaciales pueden ser pesadas.

Se recomienda cachear:

- caminos descargados;
- DEM recortado;
- productos satelitales procesados;
- series GPM descargadas.

No volver a descargar el mismo producto en cada ejecución.

---

# 72. Identificación de fuente

Cada registro derivado debe incluir:

```text
source
```

y cuando sea posible:

```text
source_product_id
```

Ejemplo:

```text
source = "copernicus_sentinel1"
```

Esto permite auditar datos.

---

# 73. Metadatos mínimos

Para un raster:

```text
source
product_id
observation_time
crs
resolution
processing_version
```

Para meteorología:

```text
source
observation_time
generated_at
```

Para caminos:

```text
source
source_feature_id
loaded_at
```

---

# 74. Calidad de datos

Durante el MVP no se implementará un sistema complejo de Data Quality.

Pero sí se verificará:

```text
nulls
rangos
CRS
geometrías inválidas
timestamps
duplicados
unidades
```

---

# 75. Duplicados

Las ingestas dinámicas deben ser idempotentes.

Ejemplo de clave lógica:

```text
segment_id
+
observation_time
+
source
```

Reejecutar el job no debería crear múltiples registros idénticos.

---

# 76. Performance

No se procesará Sentinel en tiempo real cuando el usuario abra el mapa.

El procesamiento de datos se realiza previamente.

```text
ETL / job
    ↓
features persistidas
    ↓
predicción persistida
    ↓
API
```

La API devuelve resultados ya calculados.

---

# 77. GeoJSON para frontend

FastAPI puede exponer geometrías en GeoJSON.

Ejemplo:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-58.8342, -27.4821],
      [-58.8328, -27.4817]
    ]
  },
  "properties": {
    "segment_id": 152,
    "risk_level": "CRITICAL"
  }
}
```

Recordar:

```text
GeoJSON:
[longitude, latitude]
```

no:

```text
[latitude, longitude]
```

---

# 78. Relación con Google Maps / Leaflet / MapLibre

La aplicación puede utilizar cualquier mapa base.

El dato científico no depende del proveedor del mapa.

```text
PostGIS geometry
      ↓
GeoJSON
      ↓
Leaflet / MapLibre / Google Maps
```

Por lo tanto:

> Sentinel no predice coordenadas para Google Maps.

Las coordenadas ya existen desde el comienzo.

---

# 79. Riesgos técnicos principales

### Riesgo 1

No encontrar una capa de caminos suficientemente detallada.

Mitigación:

```text
IDECorr → OpenStreetMap fallback
```

### Riesgo 2

Procesamiento Sentinel demasiado complejo.

Mitigación:

```text
reducir AOI
usar productos/procesamientos existentes
extraer pocas features
```

### Riesgo 3

Integración SMN demasiado compleja.

Mitigación:

```text
adapter desacoplado
cache
escenario meteorológico precargado para demo
```

### Riesgo 4

Demasiados datos raster.

Mitigación:

```text
clip AOI
cache
no procesar Corrientes completo
```

---

# 80. Prioridades durante el hackathon

## P0 — obligatorio

```text
AOI
caminos
segmentos
PostGIS
elevación
pendiente
lluvia histórica/antecedente
pronóstico
una feature satelital
feature snapshot
```

## P1 — muy deseable

```text
water_change
dos buffers
automatización de descarga
```

## P2 — solo si sobra tiempo

```text
flow accumulation
más polarizaciones/features SAR
Sentinel-2
NDWI
capas hidrológicas adicionales
```

---

# 81. Criterios de aceptación de datos y GIS

La capa de datos se considera lista para integrar con ML cuando:

1. existe una AOI definida;
2. se cargaron caminos reales;
3. los caminos están segmentados;
4. cada segmento tiene geometría válida;
5. todos los datos utilizan CRS controlados;
6. se calculó elevación por segmento;
7. se calculó pendiente por segmento;
8. existe al menos una feature Sentinel-1;
9. existe lluvia antecedente agregada;
10. existe pronóstico futuro normalizado;
11. puede construirse un `feature_snapshot`;
12. el mismo `segment_id` puede mostrarse en el mapa;
13. los timestamps y fuentes quedan registrados;
14. el pipeline puede repetirse.

---

# 82. Fuente de verdad del sistema

La geometría persistida en:

```text
road_segments
```

es la referencia espacial central.

Todo procesamiento externo debe terminar asociado a ella.

```text
road_segments
     │
     ├── topographic features
     ├── satellite features
     ├── weather observations
     ├── forecasts
     └── predictions
```

---

# 83. Resumen de decisiones

### Caminos

```text
IDECorr
```

### Elevación

```text
IGN MDE-Ar v2.1
```

### Satélite

```text
Copernicus Sentinel-1
```

### Lluvia antecedente

```text
NASA GPM / IMERG
```

### Lluvia futura

```text
SMN
```

### Base geoespacial

```text
PostgreSQL + PostGIS
```

### Unidad geográfica

```text
road_segment_id
```

### Longitud inicial de segmento

```text
500 m
```

configurable.

### Buffers iniciales

```text
50 m
100 m
```

### CRS de intercambio

```text
EPSG:4326
```

### Estrategia

```text
fuentes reales
→ ETL
→ features
→ PostGIS
→ ML
```

---

# 84. Pipeline final del MVP

```text
                   IDECorr
                      │
                      ▼
                    Roads
                      │
                      ▼
                Segmentation
                      │
                      ▼
                road_segment
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
      IGN         Sentinel-1       NASA GPM
       │              │              │
 topography       water state    previous rain
       │              │              │
       └──────────────┼──────────────┘
                      │
                      ▼
                     SMN
                      │
                 future rain
                      │
                      ▼
              Feature Engineering
                      │
                      ▼
               Feature Snapshot
                      │
                      ▼
                    Model
                      │
                      ▼
                  Risk Score
                      │
                      ▼
                Última Ventana
                      │
                      ▼
              PostGIS + FastAPI
                      │
                      ▼
                   Map UI
```

---

# 85. Referencias oficiales

## IDECorr

Geoservicios:

https://ide.corrientes.gob.ar/articulo/geoservicios

## Instituto Geográfico Nacional

MDE-Ar:

https://www.ign.gob.ar/content/nuevo-modelo-digital-de-elevaciones-de-la-rep%25C3%25BAblica-argentina

Documentación MDE:

https://www.ign.gob.ar/NuestrasActividades/Geodesia/ModeloDigitalElevaciones/Documentacion

## Copernicus Data Space

Portal:

https://dataspace.copernicus.eu/

Sentinel-1:

https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-1

Documentación:

https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel1.html

## NASA Earthdata / GPM

NASA Earthdata:

https://earthdata.nasa.gov/

GPM / IMERG:

https://gis.earthdata.nasa.gov/portal/home/item.html?id=598df0e6fd674ab7855f448f7f6f0e39

## Servicio Meteorológico Nacional

SMN:

https://www.smn.gob.ar/

Datos abiertos del Estado argentino:

https://www.argentina.gob.ar/node/178357

Referencia WRF-SMN Open Data:

https://www.argentina.gob.ar/noticias/el-smn-disponibiliza-los-pronosticos-numericos-3-dias-traves-de-la-nube-de-servicios-de-aws

---

# 86. Resultado esperado de esta capa

Al finalizar la implementación de datos y GIS debe ser posible ejecutar una consulta conceptual como:

```text
get_features(segment_id=152, prediction_time="2026-09-03T18:00")
```

y obtener:

```json
{
  "segment_id": 152,
  "elevation_mean_m": 48.7,
  "slope_mean_pct": 0.42,
  "rain_24h_mm": 61.4,
  "rain_72h_mm": 138.2,
  "forecast_rain_6h_mm": 34.0,
  "forecast_rain_12h_mm": 62.0,
  "water_coverage_100m_ratio": 0.27
}
```

Ese objeto constituye el contrato entre la capa de datos geoespaciales y la capa de Machine Learning.

