# Última Ventana — Machine Learning

## 1. Objetivo del documento

Este documento define la estrategia de Machine Learning del MVP de **Última Ventana**.

El objetivo no es predecir la lluvia. La lluvia futura se obtiene desde fuentes meteorológicas externas.

El modelo debe responder una pregunta distinta:

> **Dadas las condiciones meteorológicas, topográficas y satelitales de un tramo de camino, ¿qué nivel de riesgo tiene de volverse intransitable en un horizonte futuro determinado?**

La salida del modelo se transforma luego en:

```text
riesgo por segmento
        ↓
evolución temporal
        ↓
hora crítica
        ↓
Última Ventana
```

Este documento define:

- unidad de predicción;
- dataset;
- features;
- target;
- datos reales y sintéticos;
- entrenamiento;
- validación mínima;
- inferencia;
- predicción temporal;
- cálculo de riesgo;
- exportación del modelo;
- integración con backend;
- uso de Jupyter y Google Colab;
- criterios de aceptación del MVP.

---

# 2. Principio central

El modelo no recibe imágenes satelitales directamente.

El flujo recomendado para el MVP es:

```text
Sentinel-1
     ↓
procesamiento geoespacial
     ↓
features numéricas
     ↓
dataset tabular
     ↓
modelo de ML clásico
```

Por ejemplo:

```text
water_coverage_100m_ratio = 0.27
vv_backscatter_mean = -14.2
```

Estas variables se combinan con:

```text
lluvia antecedente
pronóstico futuro
elevación
pendiente
```

y pasan al modelo.

---

# 3. Tipo de problema

Para el MVP se recomienda formular el problema como:

```text
clasificación binaria
```

La variable objetivo será:

```text
intransitable_within_horizon
```

con valores:

```text
0 = no crítico / transitable
1 = crítico / intransitable
```

El horizonte temporal puede ser:

```text
3 h
6 h
12 h
```

Para simplificar el MVP se recomienda comenzar con:

```text
6 h
```

---

# 4. Por qué clasificación y no regresión

Podríamos intentar predecir directamente:

```text
horas_hasta_intransitable = 5.4
```

pero esto exige labels históricos de mucha mayor calidad.

Para un hackathon es más robusto:

```text
¿Existe riesgo de intransitabilidad dentro de las próximas 6 h?
```

y obtener:

```text
P(intransitable) = 0.82
```

Ese score puede luego utilizarse para construir una evolución temporal.

---

# 5. Alternativas futuras

En versiones posteriores podrían evaluarse:

### Regresión

```text
time_to_failure_hours
```

### Survival Analysis

```text
probabilidad de que el camino siga transitable a lo largo del tiempo
```

### Modelos espacio-temporales

Para aprender dependencia entre caminos, lluvia y territorio.

### Deep Learning

Solo si existe suficiente volumen de datos y un caso de uso que justifique trabajar directamente con imágenes.

No forman parte del MVP.

---

# 6. Unidad de predicción

La unidad fundamental será:

```text
road_segment_id
+
prediction_time
```

Ejemplo:

```text
segment_id = 152
prediction_time = 2026-09-03 18:00
```

El modelo recibe las condiciones correspondientes a ese segmento y horizonte.

---

# 7. Feature snapshot

Antes de inferencia se genera un registro completo.

Ejemplo:

```text
segment_id = 152
generated_at = 2026-09-03 12:00
prediction_time = 2026-09-03 18:00

rain_6h_mm = 14.1
rain_24h_mm = 48.3
rain_72h_mm = 118.9

forecast_rain_3h_mm = 22.4
forecast_rain_6h_mm = 39.2
forecast_rain_12h_mm = 67.5

elevation_mean_m = 51.8
slope_mean_pct = 0.72

water_coverage_50m_ratio = 0.18
water_coverage_100m_ratio = 0.26
water_change_ratio = 0.09
```

Esto se transforma en una fila del dataset de inferencia.

---

# 8. Features iniciales del MVP

El conjunto principal será:

```text
rain_6h_mm
rain_24h_mm
rain_72h_mm

forecast_rain_3h_mm
forecast_rain_6h_mm
forecast_rain_12h_mm

elevation_mean_m
slope_mean_pct

water_coverage_50m_ratio
water_coverage_100m_ratio
water_change_ratio

vv_backscatter_mean
vh_backscatter_mean
```

No todas son obligatorias en la primera iteración.

---

# 9. Feature set mínimo

Si el tiempo de desarrollo es limitado, entrenar con:

```text
rain_24h_mm
rain_72h_mm
forecast_rain_6h_mm
forecast_rain_12h_mm
elevation_mean_m
slope_mean_pct
water_coverage_100m_ratio
```

Esto representa:

```text
lluvia pasada
+
lluvia futura
+
topografía
+
estado actual del agua
```

y es suficiente para demostrar el concepto.

---

# 10. Features opcionales

Solo agregar después de tener el pipeline mínimo funcionando:

```text
rain_6h_mm
water_change_ratio
vv_backscatter_mean
vh_backscatter_mean
flow_accumulation
distance_to_water
road_type
```

La prioridad es estabilidad del pipeline y no cantidad de variables.

---

# 11. Feature engineering

El valor del modelo no depende únicamente del algoritmo.

Gran parte del rendimiento vendrá de construir variables que representen correctamente el estado hídrico del terreno.

---

# 12. Lluvia antecedente

La misma lluvia futura puede tener efectos diferentes según cuánto haya llovido antes.

Ejemplo:

### Escenario A

```text
rain_72h = 10 mm
forecast_6h = 50 mm
```

### Escenario B

```text
rain_72h = 160 mm
forecast_6h = 50 mm
```

El escenario B debería representar mayor riesgo.

Por eso se incluyen:

```text
rain_24h_mm
rain_72h_mm
```

---

# 13. Intensidad futura

Además de lluvia acumulada, el modelo debe recibir el pronóstico.

Ejemplo:

```text
forecast_rain_3h_mm
forecast_rain_6h_mm
forecast_rain_12h_mm
```

Esto permite distinguir entre eventos cortos y acumulaciones prolongadas.

---

# 14. Topografía

Las principales features serán:

```text
elevation_mean_m
slope_mean_pct
```

Un segmento bajo y prácticamente plano puede tener mayor susceptibilidad a acumular agua.

No debe interpretarse como una regla absoluta.

El modelo combina la topografía con las demás variables.

---

# 15. Features satelitales

Sentinel-1 permite obtener señales sobre el estado reciente de la superficie.

Para el MVP:

```text
water_coverage_100m_ratio
```

será la principal feature satelital.

Ejemplo:

```text
0.00 = no se detecta agua relevante
0.25 = aproximadamente 25% del entorno analizado presenta señal clasificada como agua
```

---

# 16. Water change

Si existe más de una observación:

```text
water_change_ratio =
water_coverage_current
-
water_coverage_previous
```

Ejemplo:

```text
0.31 - 0.15 = +0.16
```

Un valor positivo indica expansión reciente estimada del agua.

---

# 17. Backscatter

Si el procesamiento Sentinel lo permite se pueden incluir:

```text
vv_backscatter_mean
vh_backscatter_mean
```

Estas features deben normalizarse de manera consistente entre entrenamiento e inferencia.

No deben añadirse únicamente porque estén disponibles.

Si complican excesivamente el MVP, se pueden excluir.

---

# 18. Dataset final

Estructura recomendada:

```text
segment_id
timestamp

rain_6h_mm
rain_24h_mm
rain_72h_mm

forecast_rain_3h_mm
forecast_rain_6h_mm
forecast_rain_12h_mm

elevation_mean_m
slope_mean_pct

water_coverage_50m_ratio
water_coverage_100m_ratio
water_change_ratio

vv_backscatter_mean
vh_backscatter_mean

target
```

---

# 19. Variable objetivo

El principal problema del hackathon es la disponibilidad de:

```text
ground truth
```

Idealmente necesitaríamos observaciones históricas como:

```text
segment_id = 152
timestamp = 2025-04-14 17:00
status = INTRANSITABLE
```

y otras:

```text
segment_id = 152
timestamp = 2025-04-14 12:00
status = TRANSITABLE
```

Esto permitiría crear un target real.

---

# 20. Ground truth ideal

La tabla ideal sería:

```text
road_event
------------------------
segment_id
timestamp
status
source
```

Estados:

```text
TRANSITABLE
DIFFICULT
INTRANSITABLE
```

Para clasificación binaria:

```text
TRANSITABLE   → 0
DIFFICULT     → configurable
INTRANSITABLE → 1
```

---

# 21. Problema real del MVP

Es probable que no exista suficiente información histórica estructurada sobre el estado exacto de cada camino rural.

Por lo tanto, no se debe asumir que habrá un dataset supervisado real de alta calidad.

El MVP puede utilizar una estrategia híbrida.

---

# 22. Estrategia híbrida recomendada

Se recomienda:

```text
features reales
+
labels sintéticos / heurísticos
```

Es decir:

### Reales

```text
caminos
topografía
lluvia
Sentinel
pronóstico
```

### Sintético o aproximado

```text
target
```

Esto permite construir y demostrar el pipeline ML.

---

# 23. Qué significa un label sintético

Un label sintético se genera a partir de reglas razonables.

Ejemplo conceptual:

```text
si:
rain_72h alto
+
forecast_6h alto
+
slope baja
+
water_coverage alta

entonces:
target = 1
```

Pero esto debe considerarse una aproximación.

---

# 24. No confundir ML con conocimiento real

Si el target sintético se genera mediante reglas y luego XGBoost aprende esos labels, el modelo aprenderá principalmente:

> las reglas utilizadas para construir el dataset.

Eso es aceptable para una prueba de concepto, pero no equivale a un modelo validado sobre transitabilidad real.

---

# 25. Cómo presentarlo correctamente

Para el MVP:

> **El modelo experimental se entrena con variables territoriales reales y escenarios sintéticos físicamente plausibles. La arquitectura está preparada para recalibrarse con observaciones reales de transitabilidad.**

No afirmar:

> “El modelo predice con precisión real cuándo se corta cualquier camino de Corrientes.”

---

# 26. Generación de datos sintéticos

Se pueden generar combinaciones de variables dentro de rangos plausibles.

Ejemplo:

```text
rain_24h_mm:
0 - 200

rain_72h_mm:
0 - 400

forecast_rain_6h_mm:
0 - 150

slope_mean_pct:
0 - 10

water_coverage_100m_ratio:
0 - 1
```

Los rangos deben ajustarse según los datos reales disponibles.

---

# 27. Mejor estrategia para sintetizar

No generar todas las features aleatoriamente de forma independiente.

Preferir:

```text
muestrear sobre distribuciones observadas
```

o:

```text
tomar filas reales
+
modificar algunas variables
```

Esto produce escenarios más coherentes.

---

# 28. Ejemplo de escenario sintético

```text
rain_24h_mm = 122
rain_72h_mm = 245
forecast_rain_6h_mm = 68
forecast_rain_12h_mm = 110
elevation_mean_m = 48
slope_mean_pct = 0.3
water_coverage_100m_ratio = 0.42

target = 1
```

Otro:

```text
rain_24h_mm = 12
rain_72h_mm = 29
forecast_rain_6h_mm = 8
forecast_rain_12h_mm = 16
elevation_mean_m = 67
slope_mean_pct = 3.1
water_coverage_100m_ratio = 0.04

target = 0
```

---

# 29. Motor heurístico inicial

Antes de entrenar ML conviene tener un baseline simple.

Ejemplo conceptual:

```text
risk_score =
w1 * normalized_rain_72h
+
w2 * normalized_forecast_6h
+
w3 * normalized_water_coverage
+
w4 * low_slope_factor
+
w5 * low_elevation_factor
```

Este baseline sirve para:

- generar labels iniciales;
- comparar el modelo;
- detectar errores;
- tener fallback si el modelo falla.

---

# 30. No usar el baseline como verdad científica

Los pesos:

```text
w1
w2
w3
...
```

son parámetros del MVP.

No representan necesariamente causalidad física validada.

El objetivo es construir una aproximación operativa.

---

# 31. Modelo recomendado

Para el MVP se recomienda:

```text
XGBoost
```

Alternativa:

```text
LightGBM
```

XGBoost es suficiente y muy adecuado para:

- datos tabulares;
- features heterogéneas;
- relaciones no lineales;
- interacciones;
- datasets medianos;
- entrenamiento rápido.

---

# 32. Por qué no Deep Learning

El MVP no necesita:

- CNN;
- Transformers;
- redes neuronales complejas.

La información satelital ya se transforma en features numéricas.

Por lo tanto:

```text
XGBoost
```

es más fácil de:

- entrenar;
- explicar;
- versionar;
- integrar;
- ejecutar en backend.

---

# 33. Pipeline de entrenamiento

```text
Datos procesados
      ↓
build_training_dataset
      ↓
limpieza
      ↓
feature engineering
      ↓
train / validation split
      ↓
XGBoost
      ↓
métricas
      ↓
modelo exportado
```

---

# 34. Split del dataset

No se recomienda hacer un split puramente aleatorio si hay múltiples observaciones muy parecidas del mismo segmento y evento.

Idealmente:

```text
train
validation
```

deberían separarse por:

- fecha;
- evento;
- segmento;
- región.

Para el MVP, si el dataset es sintético, puede utilizarse un split simple, pero debe documentarse.

---

# 35. Riesgo de data leakage

Ejemplo de leakage:

Entrenar con una feature que solo estaría disponible después de que el camino ya se inundó.

Incorrecto:

```text
water_coverage tomada después del evento
```

para predecir un estado anterior.

Todas las features deben representar información disponible en:

```text
prediction_generated_at
```

o antes.

---

# 36. Leakage temporal

Si queremos predecir:

```text
riesgo a las 18:00
```

desde:

```text
12:00
```

no podemos utilizar información observada a:

```text
17:30
```

El dataset debe respetar el horizonte temporal.

---

# 37. Preprocessing

XGBoost requiere poca transformación numérica.

No es obligatorio escalar:

```text
StandardScaler
```

para la mayoría de las variables.

Sí debemos:

- controlar nulls;
- tipos;
- categorías;
- nombres;
- unidades.

---

# 38. Variables categóricas

Si se incorpora:

```text
road_type
```

por ejemplo:

```text
DIRT
GRAVEL
PAVED
```

se puede codificar mediante:

```text
OneHotEncoder
```

o una codificación compatible con el modelo.

Para el primer MVP se puede excluir esta variable si no hay datos confiables.

---

# 39. Missing values

Opciones:

### Opción A

XGBoost puede manejar valores faltantes en varias situaciones.

### Opción B

Imputar:

```text
median
```

### Recomendación MVP

Mantener una estrategia explícita y consistente.

No rellenar:

```text
0
```

por defecto si cero tiene significado real.

---

# 40. Feature schema

Debe existir un archivo:

```text
models/feature_schema_v1.json
```

Ejemplo:

```json
{
  "version": "v1",
  "features": [
    "rain_24h_mm",
    "rain_72h_mm",
    "forecast_rain_6h_mm",
    "forecast_rain_12h_mm",
    "elevation_mean_m",
    "slope_mean_pct",
    "water_coverage_100m_ratio"
  ]
}
```

---

# 41. Orden de features

El backend debe enviar las mismas variables que se utilizaron durante entrenamiento.

Por eso el feature schema es un contrato.

No depender de:

```text
orden accidental de columnas
```

---

# 42. Modelo versionado

Ejemplo:

```text
models/
├── model_v1.json
├── feature_schema_v1.json
└── metadata_v1.json
```

---

# 43. Metadata

Ejemplo:

```json
{
  "model_version": "v1",
  "algorithm": "xgboost",
  "target": "intransitable_within_6h",
  "critical_threshold": 0.70,
  "feature_schema": "v1",
  "training_data_type": "hybrid_real_synthetic"
}
```

---

# 44. Hiperparámetros iniciales

No realizar una búsqueda exhaustiva.

Ejemplo razonable:

```text
n_estimators = 200
max_depth = 4
learning_rate = 0.05
subsample = 0.8
colsample_bytree = 0.8
```

Estos valores son iniciales.

El objetivo del hackathon no es optimizar décimas de métrica.

---

# 45. Evaluación mínima

Aunque sea un MVP, no se recomienda entrenar y confiar ciegamente.

La validación puede ser simple.

Métricas:

```text
precision
recall
F1
ROC-AUC
```

---

# 46. Métrica más relevante

Para este caso, un falso negativo puede ser más costoso que un falso positivo.

Ejemplo:

```text
modelo dice seguro
pero camino queda intransitable
```

Por lo tanto, interesa especialmente:

```text
recall de la clase crítica
```

---

# 47. Trade-off

### Falso positivo

```text
el sistema alerta
pero finalmente el camino sigue transitable
```

Costo:

- precaución innecesaria;
- posible movimiento anticipado.

### Falso negativo

```text
el sistema no alerta
pero el camino se vuelve intransitable
```

Costo potencial:

- productor aislado;
- ganado o producción sin retirar;
- vehículo bloqueado.

Para un sistema preventivo, se puede preferir sensibilidad.

---

# 48. Threshold

El modelo devuelve:

```text
probability
```

Ejemplo:

```text
0.63
```

No necesariamente se utilizará:

```text
0.50
```

como umbral.

Para Última Ventana se define un threshold operativo.

Ejemplo:

```text
CRITICAL_RISK_THRESHOLD = 0.70
```

---

# 49. Niveles de riesgo

El backend puede mapear:

```text
0.00 - 0.30 → LOW
0.30 - 0.50 → MODERATE
0.50 - 0.70 → HIGH
0.70 - 1.00 → CRITICAL
```

Estos rangos son configurables.

---

# 50. Interpretación del risk score

No presentar:

```text
0.82
```

necesariamente como:

> “82% real de probabilidad física”.

Si el modelo se entrenó con labels sintéticos, el score es mejor interpretarlo como:

> **índice o score estimado de riesgo generado por el modelo experimental.**

Una vez calibrado con datos reales, podrá adquirir una interpretación probabilística más fuerte.

---

# 51. Baseline

Antes de aceptar XGBoost como modelo final, comparar contra:

```text
heuristic baseline
```

o:

```text
Logistic Regression
```

Si XGBoost no mejora el baseline, revisar datos y features.

---

# 52. Interpretabilidad

Para el pitch puede utilizarse:

```text
feature importance
```

o:

```text
SHAP
```

para explicar qué variables influyeron.

Ejemplo:

```text
Factores principales:

+ forecast_rain_6h
+ rain_72h
+ water_coverage_100m
+ pendiente baja
```

No es obligatorio implementar SHAP en producción.

---

# 53. SHAP

Si hay tiempo:

```text
shap.TreeExplainer
```

puede generar explicaciones por predicción.

Esto permitiría mostrar:

> “El riesgo aumenta principalmente por lluvia acumulada alta y agua detectada alrededor del camino.”

Es una mejora muy buena para la demo.

---

# 54. Jupyter Notebook

Sí se recomienda utilizar Jupyter.

Los notebooks sirven para:

- exploración;
- análisis;
- generación de dataset;
- pruebas;
- entrenamiento;
- métricas;
- gráficos;
- explicabilidad.

---

# 55. Google Colab

Sí se recomienda Google Colab para la parte de ML.

Ventajas:

- entorno reproducible;
- no requiere configurar Python localmente;
- fácil colaboración;
- notebooks compartibles;
- suficiente capacidad para XGBoost.

No es necesario utilizar GPU.

---

# 56. Notebooks recomendados

```text
notebooks/

00_exploracion_dataset.ipynb
01_generacion_sinteticos.ipynb
02_feature_engineering.ipynb
03_training_xgboost.ipynb
04_evaluation.ipynb
05_explainability.ipynb
```

---

# 57. Regla para notebooks

No dejar toda la lógica únicamente dentro de notebooks.

Cuando una función quede estable:

```text
mover a src/
```

Ejemplo:

```text
src/ml/
src/features/
```

---

# 58. Módulos Python

Estructura:

```text
src/
├── features/
│   ├── builder.py
│   └── schema.py
│
└── ml/
    ├── dataset.py
    ├── train.py
    ├── evaluate.py
    ├── predictor.py
    └── synthetic.py
```

---

# 59. `dataset.py`

Responsabilidades:

- cargar dataset;
- seleccionar features;
- separar X/y;
- controlar tipos;
- validar columnas.

---

# 60. `synthetic.py`

Responsabilidades:

- generar escenarios;
- aplicar reglas de target;
- controlar rangos;
- registrar versión de generador.

Ejemplo:

```text
synthetic_generator_version = v1
```

---

# 61. `train.py`

Responsabilidades:

```text
load dataset
validate schema
split data
train XGBoost
evaluate
save model
save metadata
```

---

# 62. `predictor.py`

Responsabilidades:

```text
load model
load schema
validate input
predict_proba
return risk_score
```

Contrato:

```python
predict(features: dict) -> float
```

---

# 63. Integración con backend

FastAPI no entrena el modelo.

Flujo:

```text
backend inicia
    ↓
carga model_v1.json
    ↓
espera features
    ↓
predictor.predict()
    ↓
risk_score
```

---

# 64. Inferencia

Ejemplo:

```text
features =
{
    rain_24h_mm: 61.4,
    rain_72h_mm: 138.2,
    forecast_rain_6h_mm: 34.0,
    forecast_rain_12h_mm: 62.0,
    elevation_mean_m: 48.7,
    slope_mean_pct: 0.42,
    water_coverage_100m_ratio: 0.27
}
```

Modelo:

```text
risk_score = 0.78
```

Resultado:

```text
risk_level = CRITICAL
```

---

# 65. Predicción temporal

Última Ventana necesita más que una única predicción.

Se debe ejecutar el modelo para distintos horizontes.

Ejemplo:

```text
14:00 → 0.24
15:00 → 0.31
16:00 → 0.46
17:00 → 0.61
18:00 → 0.74
19:00 → 0.85
```

---

# 66. Cómo construir cada horizonte

Las features estáticas permanecen:

```text
elevation
slope
```

Las features dinámicas cambian:

```text
forecast_rain
rain accumulation
```

Por cada `prediction_time` se genera un feature snapshot diferente.

---

# 67. Ejemplo

A las 12:00:

```text
prediction_time = 15:00
forecast_rain_3h = 18 mm
forecast_rain_6h = 31 mm
```

Luego:

```text
prediction_time = 18:00
forecast_rain_3h = 26 mm
forecast_rain_6h = 54 mm
```

Se ejecuta el mismo modelo con distintos snapshots.

---

# 68. Hora crítica

El backend busca:

```text
primer horario
donde
risk_score >= CRITICAL_RISK_THRESHOLD
```

Ejemplo:

```text
18:00
```

Entonces:

```text
critical_time = 18:00
```

---

# 69. Última Ventana

Machine Learning no debe calcular directamente la Última Ventana.

El modelo solo calcula:

```text
risk_score
```

La lógica de negocio calcula:

```text
critical_time
-
travel_time
-
safety_margin
```

---

# 70. Separación de responsabilidades

```text
ML
→ riesgo

Backend
→ hora crítica

Backend
→ tiempo de recorrido

Backend
→ margen de seguridad

Backend
→ Última Ventana
```

Esto evita mezclar lógica de producto con entrenamiento.

---

# 71. Ejemplo completo

Modelo:

```text
14:00 → 0.32
15:00 → 0.41
16:00 → 0.52
17:00 → 0.64
18:00 → 0.76
```

Threshold:

```text
0.70
```

Resultado:

```text
critical_time = 18:00
```

Ruta:

```text
travel_time = 80 min
safety_margin = 40 min
```

Última Ventana:

```text
18:00 - 120 min = 16:00
```

Salida:

> **Última salida recomendada: 16:00.**

---

# 72. Predicción por ruta

Un recorrido puede tener múltiples segmentos.

Cada segmento tiene su curva de riesgo.

Ejemplo:

```text
segment 101 → crítico 21:00
segment 102 → crítico 18:00
segment 103 → crítico 20:00
```

El cuello de botella es:

```text
segment 102
```

---

# 73. Segmento crítico

Definición:

```text
critical_segment =
segmento de la ruta cuya hora crítica ocurre primero
```

Esto se utiliza para calcular la Última Ventana del recorrido.

---

# 74. Datos de training vs datos de producción

Deben utilizar exactamente la misma lógica de features.

Incorrecto:

```text
training:
rain_24h

production:
rain_last_day
```

aunque conceptualmente parezcan iguales.

Debe existir una sola función:

```text
build_features()
```

---

# 75. Training-serving skew

Este problema ocurre cuando:

```text
features de entrenamiento
!=
features de producción
```

Debe evitarse mediante:

- schemas versionados;
- código compartido;
- tests;
- nombres estables.

---

# 76. Reentrenamiento

El MVP no necesita reentrenamiento automático.

Flujo:

```text
nuevo dataset
    ↓
notebook / train.py
    ↓
model_v2
    ↓
evaluación
    ↓
deploy manual
```

---

# 77. Mejora futura con datos reales

La aplicación puede permitir reportes:

```text
TRANSITABLE
DIFFICULT
INTRANSITABLE
```

Cada reporte genera:

```text
road_event
```

Con el tiempo:

```text
road_events
+
features históricas
```

se convierten en un dataset real.

---

# 78. Active learning futuro

Podría priorizarse la recolección de labels en:

- segmentos de alta incertidumbre;
- caminos críticos;
- eventos de lluvia intensa.

No forma parte del MVP.

---

# 79. Monitoreo de modelo

Para el hackathon basta registrar:

```text
model_version
feature_schema_version
risk_score
generated_at
```

En producción real deberían agregarse:

- drift;
- calibration;
- performance;
- data quality.

---

# 80. Reproducibilidad

El entrenamiento debe guardar:

```text
random_seed
model params
features
dataset version
model version
```

Ejemplo:

```text
seed = 42
```

---

# 81. Dataset versionado

Ejemplo:

```text
data/processed/training_dataset_v1.parquet
```

y metadata:

```text
training_dataset_v1.json
```

---

# 82. Formato de dataset

Se recomienda:

```text
Parquet
```

porque conserva tipos y es eficiente.

CSV puede usarse para inspección manual.

---

# 83. Artifact de modelo

XGBoost puede exportarse como:

```text
JSON
```

Ejemplo:

```text
model_v1.json
```

Esto es preferible a depender exclusivamente de `pickle`.

---

# 84. Test de integración del modelo

Debe existir un feature snapshot conocido.

Ejemplo:

```text
tests/fixtures/sample_features.json
```

Se ejecuta:

```text
predict(sample_features)
```

y se verifica:

```text
0 <= risk_score <= 1
```

---

# 85. Tests mínimos

### Schema

```text
faltan features → error
```

### Tipo

```text
rain_24h = "hola" → error
```

### Rango

```text
water_coverage = 1.8 → error
```

### Predictor

```text
modelo carga correctamente
```

### Determinismo

La misma entrada debe devolver el mismo resultado para el mismo modelo.

---

# 86. Validación mínima del dataset

Antes de entrenar:

```text
no duplicados obvios
target válido
columnas presentes
rangos razonables
nulls conocidos
```

---

# 87. Desbalance de clases

Podría existir:

```text
muchos casos seguros
pocos críticos
```

Opciones:

- class weights;
- `scale_pos_weight`;
- undersampling;
- oversampling.

Para el MVP:

```text
scale_pos_weight
```

puede ser suficiente.

---

# 88. No usar accuracy como única métrica

Ejemplo:

```text
95% caminos seguros
```

Un modelo que siempre diga:

```text
seguro
```

tendría:

```text
95% accuracy
```

pero sería inútil.

Por eso evaluar:

```text
precision
recall
F1
ROC-AUC
```

---

# 89. Matriz de confusión

Debe incluirse en el notebook de evaluación.

```text
               Predicho
             0        1

Real 0      TN       FP
Real 1      FN       TP
```

Especial atención:

```text
FN
```

---

# 90. Calibración

Un modelo puede ordenar riesgos correctamente sin que:

```text
0.80
```

signifique literalmente 80%.

Para el MVP no es obligatorio calibrar.

En una versión posterior:

```text
CalibratedClassifierCV
```

podría utilizarse.

---

# 91. Cómo mostrar el score en frontend

Si el modelo es experimental:

Preferir:

```text
Riesgo: ALTO
Score: 0.78
```

en vez de:

> “Probabilidad exacta: 78%”.

Esto evita sobreinterpretar el modelo.

---

# 92. Explicación de predicción

Ejemplo de salida:

```text
risk_score = 0.78

factores principales:
- lluvia acumulada elevada
- lluvia intensa prevista
- agua detectada alrededor
- pendiente baja
```

Esta explicación puede provenir de:

- reglas;
- feature importance;
- SHAP.

---

# 93. Fallback si ML no está listo

El sistema debe poder seguir funcionando con:

```text
heuristic risk engine
```

Esto es importante para la hackathon.

Si el modelo falla a último momento:

```text
features
   ↓
heuristic engine
   ↓
risk score
```

y el resto del producto continúa.

---

# 94. Arquitectura híbrida recomendada

Para el hackathon:

```text
                     Features
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
       Heuristic Engine         XGBoost
             │                     │
             └──────────┬──────────┘
                        ▼
                   Risk Score
```

En la demo principal se utiliza XGBoost.

El baseline sirve como respaldo.

---

# 95. Modo demo

El sistema debe soportar un escenario controlado.

Ejemplo:

```text
demo_scenario_01.json
```

con:

```text
pronóstico fuerte
+
lluvia acumulada
+
features reales del territorio
```

Esto garantiza que pueda demostrarse la evolución del riesgo aunque el día de la hackathon no llueva.

---

# 96. Qué es real en la demo

Idealmente:

```text
geometría → real
topografía → real
Sentinel → real
GPM → real
```

Mientras:

```text
pronóstico
```

puede ser:

```text
histórico
o
simulado
```

si se necesita controlar la demostración.

---

# 97. Qué no hacer

No entrenar con:

```text
datos completamente aleatorios
```

sin relación con el territorio.

No afirmar:

```text
precisión real
```

si el target es sintético.

No incorporar:

```text
20 algoritmos
```

solo para comparar.

No utilizar:

```text
deep learning
```

porque “parece más avanzado”.

No utilizar:

```text
imágenes sin georreferenciación
```

para relacionarlas manualmente con caminos.

---

# 98. Orden de implementación ML

## Paso 1

Construir dataset con features reales.

## Paso 2

Analizar distribuciones.

## Paso 3

Implementar baseline heurístico.

## Paso 4

Generar labels / escenarios sintéticos.

## Paso 5

Entrenar XGBoost.

## Paso 6

Evaluar.

## Paso 7

Exportar modelo.

## Paso 8

Construir `predictor.py`.

## Paso 9

Integrar con FastAPI.

## Paso 10

Ejecutar predicción temporal.

---

# 99. Notebook 00 — Exploración

Debe responder:

- cuántas filas;
- rangos;
- nulls;
- distribuciones;
- correlaciones básicas;
- posibles anomalías.

---

# 100. Notebook 01 — Sintéticos

Debe documentar:

- reglas;
- rangos;
- número de escenarios;
- distribución target;
- versión de generador.

---

# 101. Notebook 02 — Features

Debe:

- cargar datos;
- construir feature matrix;
- comprobar tipos;
- exportar dataset final.

---

# 102. Notebook 03 — Training

Debe:

- cargar dataset;
- split;
- entrenar XGBoost;
- guardar modelo.

---

# 103. Notebook 04 — Evaluation

Debe mostrar:

- confusion matrix;
- precision;
- recall;
- F1;
- ROC-AUC;
- threshold analysis.

---

# 104. Notebook 05 — Explainability

Opcional.

Puede mostrar:

```text
feature importance
SHAP summary
SHAP para un caso concreto
```

---

# 105. Estructura de Colab

Los notebooks pueden montar Google Drive:

```text
/content/drive/
```

pero el repositorio debe seguir siendo la fuente del código.

Recomendación:

```text
git clone repo
```

y ejecutar funciones desde `src/`.

---

# 106. Dependencias ML

Ejemplo:

```text
pandas
numpy
scikit-learn
xgboost
shap
matplotlib
joblib
pyarrow
```

GeoPandas/Rasterio pertenecen principalmente a la capa de datos pero pueden instalarse en Colab cuando sea necesario.

---

# 107. Archivo de configuración

Ejemplo:

```text
config/ml.yaml
```

con:

```yaml
model:
  algorithm: xgboost
  version: v1

target:
  name: intransitable_within_6h

thresholds:
  critical: 0.70

features:
  schema_version: v1
```

---

# 108. API de predictor

Conceptualmente:

```python
class RiskPredictor:
    def predict(self, features: dict) -> float:
        ...
```

No devolver desde este componente:

```text
last_safe_departure
```

porque pertenece al dominio del backend.

---

# 109. Batch inference

Para eficiencia:

```text
predict_many(feature_snapshots)
```

El sistema puede predecir cientos de segmentos en un solo batch.

---

# 110. Formato de salida batch

Ejemplo:

```text
segment_id | prediction_time | risk_score
------------------------------------------
151        | 18:00           | 0.43
152        | 18:00           | 0.78
153        | 18:00           | 0.55
```

Se persiste en:

```text
risk_predictions
```

---

# 111. Predicción horaria

Para el MVP se puede analizar:

```text
próximas 12 h
```

en pasos de:

```text
1 h
```

Ejemplo:

```text
12 predicciones por segmento
```

Si hay:

```text
200 segmentos
```

resultan:

```text
2400 predicciones
```

XGBoost puede manejar esto sin dificultad.

---

# 112. Horizon

Parámetro:

```text
PREDICTION_HORIZON_HOURS = 12
```

configurable.

---

# 113. Granularidad temporal

Parámetro:

```text
PREDICTION_STEP_HOURS = 1
```

Para la hackathon:

```text
1 h
```

es suficientemente claro.

---

# 114. Margen de seguridad

No forma parte del ML.

Ejemplo:

```text
SAFETY_MARGIN_MINUTES = 40
```

configurable en backend.

---

# 115. Confianza vs riesgo

No mezclar:

```text
risk_score
```

con:

```text
model_confidence
```

Si se desea mostrar confianza del modelo, debe definirse por separado.

Para el MVP no es necesario.

---

# 116. Model card mínima

Se recomienda guardar:

```text
docs/model_card_v1.md
```

con:

- algoritmo;
- features;
- target;
- origen de datos;
- uso de sintéticos;
- limitaciones;
- versión.

Puede crearse después del entrenamiento.

---

# 117. Limitaciones que deben documentarse

- labels sintéticos;
- cobertura geográfica limitada;
- resolución espacial heterogénea;
- Sentinel no disponible en tiempo real continuo;
- GPM con resolución regional;
- modelo aún no calibrado con suficientes eventos reales.

---

# 118. Cómo comunicarlo en el pitch

Buena formulación:

> “El MVP utiliza un modelo de riesgo entrenado sobre variables meteorológicas y geoespaciales, apoyado en escenarios sintéticos para suplir la falta inicial de históricos estructurados de transitabilidad. La arquitectura permite incorporar reportes reales y recalibrar el modelo progresivamente.”

---

# 119. Evolución productiva

Después de la hackathon:

```text
reportes reales
+
datos históricos
+
eventos meteorológicos
        ↓
nuevo dataset
        ↓
reentrenamiento
        ↓
calibración regional
```

---

# 120. Criterios de aceptación del módulo ML

Se considera listo cuando:

1. existe un dataset tabular reproducible;
2. las features coinciden con el schema v1;
3. existe un target documentado;
4. se documenta qué parte es sintética;
5. existe baseline;
6. XGBoost entrena;
7. se calculan métricas;
8. el modelo se exporta;
9. `predictor.py` puede cargarlo;
10. una feature snapshot genera un `risk_score`;
11. se puede ejecutar batch inference;
12. se generan predicciones temporales;
13. el backend puede consumirlas;
14. el modelo y las features están versionados.

---

# 121. Feature schema v1 propuesto

Primera versión recomendada:

```text
rain_24h_mm
rain_72h_mm
forecast_rain_6h_mm
forecast_rain_12h_mm
elevation_mean_m
slope_mean_pct
water_coverage_100m_ratio
```

Esta debe ser la primera versión funcional.

Después puede evolucionar a:

```text
feature_schema_v2
```

con:

```text
rain_6h_mm
forecast_rain_3h_mm
water_coverage_50m_ratio
water_change_ratio
vv_backscatter_mean
vh_backscatter_mean
```

---

# 122. Target v1 propuesto

```text
target:
intransitable_within_6h
```

Valores:

```text
0
1
```

Interpretación:

> indicador experimental de si el tramo alcanzaría condiciones de intransitabilidad o riesgo crítico dentro de las próximas seis horas.

---

# 123. Modelo v1

```text
algorithm = XGBoost
```

Salida:

```text
risk_score ∈ [0, 1]
```

---

# 124. Threshold v1

```text
LOW:
0.00 - 0.30

MODERATE:
0.30 - 0.50

HIGH:
0.50 - 0.70

CRITICAL:
0.70 - 1.00
```

Estos valores deben tratarse como parámetros del MVP.

---

# 125. Arquitectura ML final

```text
                DATOS REALES
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
meteorología     topografía      Sentinel
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
              Feature Engineering
                     │
                     ▼
             Dataset tabular
                     │
             ┌───────┴────────┐
             │                │
             ▼                ▼
      labels reales      labels sintéticos
             │                │
             └───────┬────────┘
                     ▼
                   XGBoost
                     │
                     ▼
                model_v1.json
                     │
                     ▼
                 FastAPI
                     │
                     ▼
              Feature Snapshot
                     │
                     ▼
                Risk Score
                     │
                     ▼
             Predicción temporal
                     │
                     ▼
                Hora crítica
                     │
                     ▼
              Última Ventana
```

---

# 126. Resumen ejecutivo de ML

Para el MVP:

```text
1. No predecimos lluvia.
2. La lluvia es una entrada.
3. No usamos imágenes directamente en XGBoost.
4. Extraemos features geoespaciales de Sentinel.
5. Construimos un dataset tabular.
6. Usamos datos reales siempre que sea posible.
7. Podemos utilizar labels sintéticos para demostrar el pipeline.
8. Entrenamos XGBoost.
9. El modelo devuelve un risk_score.
10. Ejecutamos el modelo para varias horas futuras.
11. Detectamos el primer horario crítico.
12. El backend calcula Última Ventana.
```

---

# 127. Decisión final para el hackathon

La estrategia recomendada es:

```text
Jupyter + Google Colab
        ↓
exploración
+
dataset
+
sintéticos
+
training
+
evaluation
        ↓
XGBoost model_v1.json
        ↓
FastAPI
        ↓
predicción por segmento
        ↓
Última Ventana
```

Esta separación permite desarrollar Machine Learning rápidamente sin convertir los notebooks en parte del sistema productivo.

---

# 128. Resultado esperado

Al finalizar esta etapa, debe ser posible ejecutar:

```python
risk = predictor.predict({
    "rain_24h_mm": 61.4,
    "rain_72h_mm": 138.2,
    "forecast_rain_6h_mm": 34.0,
    "forecast_rain_12h_mm": 62.0,
    "elevation_mean_m": 48.7,
    "slope_mean_pct": 0.42,
    "water_coverage_100m_ratio": 0.27
})
```

y obtener:

```text
risk = 0.78
```

Luego el backend interpreta:

```text
0.78 → CRITICAL
```

y utiliza la serie temporal de predicciones para calcular la hora crítica y la Última Ventana.

---

# 129. Definición resumida

> **El módulo de Machine Learning de Última Ventana utiliza variables meteorológicas, topográficas y satelitales asociadas a cada tramo de camino para estimar un score de riesgo de intransitabilidad. El modelo se ejecuta sobre distintos horizontes futuros y sus resultados alimentan el motor de decisión que calcula la hora crítica y la última salida recomendada.**

