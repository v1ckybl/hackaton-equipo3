# Última Ventana — Producto y Funcionalidad

## 1. Resumen ejecutivo

**Última Ventana** es un sistema de apoyo a la toma de decisiones para zonas rurales expuestas a lluvias intensas e inundaciones. Su objetivo es transformar información meteorológica y territorial en una recomendación concreta y accionable:

> **¿Hasta qué momento conviene utilizar un camino rural antes de que el riesgo de intransitabilidad sea demasiado alto?**

La solución busca anticipar problemas de acceso y salida en establecimientos rurales, permitiendo que productores, empresas agropecuarias, transportistas u organismos públicos puedan adelantar el movimiento de producción, ganado, maquinaria o vehículos antes de que un camino quede comprometido por anegamiento.

El producto no pretende indicar con certeza exacta el momento en que un camino quedará inutilizable. Para el MVP, calcula un **riesgo estimado de intransitabilidad** y determina una **última hora recomendada de salida** considerando la evolución esperada del riesgo, el tiempo necesario para completar el trayecto y un margen preventivo.

---

## 2. Problema

Durante eventos de lluvias intensas, muchos caminos rurales pueden deteriorarse rápidamente, anegarse o quedar temporalmente intransitables.

Actualmente, una alerta meteorológica puede informar que se esperan precipitaciones fuertes, pero no responde preguntas operativas como:

- ¿Qué caminos concretos tienen mayor riesgo?
- ¿En qué tramo del camino está el problema?
- ¿Cuánto tiempo queda antes de que el riesgo sea crítico?
- ¿Conviene retirar producción o ganado ahora?
- ¿Hasta qué hora todavía sería recomendable salir?
- ¿Qué camino representa el punto más vulnerable de una ruta de salida?

El problema central es que una predicción meteorológica describe el evento climático, pero no necesariamente traduce ese evento en una **decisión logística específica**.

Última Ventana busca cubrir esa brecha.

---

## 3. Propuesta de valor

La propuesta de valor se resume en:

> **Mientras un pronóstico dice cuánto puede llover, Última Ventana estima cuánto tiempo queda para actuar.**

El sistema cruza información del territorio y condiciones meteorológicas para calcular el riesgo de cada tramo de camino.

Ejemplo:

- Camino A: riesgo bajo.
- Camino B: riesgo moderado.
- Camino C: riesgo alto en aproximadamente 5 horas.

En lugar de mostrar solamente:

> “Se esperan 90 mm de lluvia.”

el sistema intenta generar una salida operativa:

> **Última salida recomendada: 16:00.**

Esto convierte información climática abstracta en una decisión logística concreta.

---

## 4. Usuario objetivo

### Usuario principal

Productor rural o responsable operativo de un establecimiento agropecuario.

Puede necesitar mover:

- ganado;
- producción agrícola;
- madera;
- maquinaria;
- insumos;
- vehículos;
- personal.

### Usuarios secundarios

La misma información podría ser utilizada posteriormente por:

- empresas agropecuarias;
- empresas forestales;
- transportistas;
- cooperativas;
- municipios;
- Defensa Civil;
- organismos provinciales;
- aseguradoras;
- operadores logísticos.

El MVP se enfocará principalmente en el **productor rural**.

---

## 5. Objetivo general

Desarrollar un sistema capaz de estimar el riesgo de intransitabilidad de caminos rurales ante eventos de lluvia y calcular una ventana temporal recomendada para completar movimientos logísticos antes de alcanzar condiciones consideradas críticas.

---

## 6. Objetivos específicos

1. Representar caminos rurales geográficamente y dividirlos en segmentos analizables.
2. Asociar a cada segmento información meteorológica, topográfica y satelital.
3. Calcular un nivel de riesgo para diferentes momentos futuros.
4. Detectar el primer momento en el que el riesgo supera un umbral crítico.
5. Calcular la última hora recomendada de salida.
6. Mostrar los resultados sobre un mapa interactivo.
7. Emitir alertas preventivas cuando una ruta o camino alcance niveles relevantes de riesgo.
8. Explicar de forma simple por qué un segmento presenta riesgo elevado.

---

## 7. Alcance del MVP

El MVP debe demostrar que el concepto funciona de extremo a extremo.

Debe permitir:

- trabajar sobre una región rural acotada de Corrientes;
- cargar una red de caminos;
- dividir caminos en segmentos;
- asociar condiciones meteorológicas y territoriales;
- ejecutar un modelo o motor de riesgo;
- obtener riesgo por segmento;
- proyectar el riesgo para diferentes horas futuras;
- determinar una hora crítica;
- calcular una Última Ventana;
- visualizar caminos según nivel de riesgo;
- consultar detalles de un camino;
- mostrar una alerta preventiva.

No es necesario cubrir toda la provincia de Corrientes para demostrar el concepto.

---

## 8. Fuera del alcance inicial

El MVP no necesita resolver todavía:

- toda la red vial rural provincial;
- navegación GPS turn-by-turn;
- predicción hidráulica de alta precisión;
- simulaciones físicas completas de inundación;
- integración con todos los organismos públicos;
- aplicación móvil nativa;
- sistema completo de gestión de emergencias;
- cálculo económico de pérdidas;
- rutas logísticas de múltiples vehículos;
- predicción exacta del momento de corte;
- calibración definitiva del modelo con años de observaciones reales.

Estas capacidades pueden formar parte de versiones posteriores.

---

## 9. Concepto de funcionamiento

El sistema sigue el flujo:

```text
Fuentes externas
      ↓
Datos meteorológicos y territoriales
      ↓
Segmentos de caminos
      ↓
Feature engineering
      ↓
Modelo / motor de riesgo
      ↓
Riesgo por segmento y por hora
      ↓
Detección de hora crítica
      ↓
Cálculo de Última Ventana
      ↓
Mapa + alerta + recomendación
```

---

## 10. Concepto de segmento de camino

La unidad central del sistema no es necesariamente un camino completo.

Un camino puede tener kilómetros en buenas condiciones y un pequeño tramo situado en una depresión o próximo a un curso de agua.

Por eso se divide cada camino en segmentos.

Ejemplo:

```text
Camino Rural 12

Segmento 1 → km 0,0 a 0,5
Segmento 2 → km 0,5 a 1,0
Segmento 3 → km 1,0 a 1,5
Segmento 4 → km 1,5 a 2,0
```

Cada segmento posee un identificador único:

```text
road_segment_id
```

Este identificador permite vincular:

- geometría;
- topografía;
- información satelital;
- meteorología;
- features;
- predicciones;
- alertas.

---

## 11. Entradas funcionales

El sistema utiliza diferentes grupos de información.

### 11.1 Caminos

Permiten determinar:

- ubicación;
- geometría;
- longitud;
- segmentos;
- conexiones entre caminos.

### 11.2 Meteorología

Permite conocer:

- lluvia reciente;
- lluvia acumulada;
- pronóstico futuro;
- intensidad esperada.

Ejemplos conceptuales:

```text
rain_6h
rain_24h
rain_72h
forecast_rain_3h
forecast_rain_6h
forecast_rain_12h
```

### 11.3 Información satelital

Permite representar el estado reciente de la superficie.

Puede utilizarse para derivar variables como:

- presencia de agua;
- extensión de agua;
- cambios de cobertura;
- proximidad de agua al camino.

La imagen satelital está georreferenciada, por lo que sus observaciones pueden asociarse a los mismos segmentos que luego aparecen en el mapa.

### 11.4 Topografía

Permite representar:

- elevación;
- pendiente;
- zonas bajas;
- tendencia a acumulación de agua.

### 11.5 Características del camino

Cuando estén disponibles:

- tipo de superficie;
- tierra;
- ripio;
- pavimento;
- estado general.

---

## 12. Salidas funcionales

El sistema genera cuatro salidas principales.

### 12.1 Riesgo por segmento

Ejemplo:

```text
Segmento 101 → 18%
Segmento 102 → 37%
Segmento 103 → 76%
Segmento 104 → 89%
```

### 12.2 Nivel de riesgo

Para el MVP se puede utilizar una clasificación simple:

```text
0% – 30%   → Bajo
30% – 50%  → Moderado
50% – 70%  → Alto
70% – 100% → Crítico
```

Los valores definitivos son parámetros ajustables.

### 12.3 Hora crítica estimada

Es el primer momento futuro en el que un segmento alcanza el umbral considerado crítico.

Ejemplo:

```text
14:00 → 22%
15:00 → 31%
16:00 → 48%
17:00 → 62%
18:00 → 74% ← primer momento crítico
19:00 → 86%
```

Resultado:

```text
Hora crítica estimada: 18:00
```

### 12.4 Última Ventana

A partir de la hora crítica, el sistema calcula hasta cuándo conviene comenzar el recorrido.

Ejemplo:

```text
Hora crítica:        18:00
Tiempo de recorrido: 01:20
Margen preventivo:   00:40
--------------------------------
Última salida:       16:00
```

Resultado mostrado al usuario:

> **Última salida recomendada: 16:00.**

---

## 13. Definición de Última Ventana

La Última Ventana representa la hora máxima recomendada para iniciar un movimiento logístico antes de que el recorrido alcance condiciones de riesgo elevado.

Conceptualmente:

```text
Última Ventana =
Hora crítica estimada
- tiempo de recorrido
- margen de seguridad
```

El margen preventivo permite evitar que la recomendación se base exactamente en el límite del modelo.

---

## 14. Riesgo de una ruta completa

Una ruta puede atravesar varios caminos o segmentos.

Ejemplo:

```text
Campo
  ↓
Segmento A
  ↓
Segmento B
  ↓
Segmento C
  ↓
Ruta provincial
```

Supongamos:

```text
Segmento A → crítico en 12 h
Segmento B → crítico en 5 h
Segmento C → crítico en 9 h
```

La ventana logística está condicionada por el segmento que se vuelve crítico primero.

Por lo tanto:

> **El tramo más vulnerable determina la ventana operativa de la ruta.**

Esto evita informar solamente cuánto tiempo permanece utilizable cada camino de forma aislada.

---

## 15. Mapa de riesgo

El frontend mostrará los caminos sobre un mapa interactivo.

Representación sugerida:

```text
🟢 Bajo
🟡 Moderado
🟠 Alto
🔴 Crítico
```

Cada segmento puede cambiar de apariencia según su predicción actual o futura.

El mapa permite detectar visualmente:

- caminos seguros;
- caminos comprometidos;
- puntos críticos;
- posibles corredores de salida.

---

## 16. Detalle de un camino

Al seleccionar un camino o segmento, el usuario debe poder visualizar información resumida.

Ejemplo:

```text
Camino Rural 27

Riesgo actual: 42%
Nivel: Moderado

Riesgo previsto a las 18:00: 78%
Nivel previsto: Crítico

Hora crítica estimada: 18:00
Última salida recomendada: 16:00

Factores relevantes:
- lluvia prevista elevada;
- zona topográficamente baja;
- agua detectada próxima al tramo.
```

La información debe ser entendible para un usuario no técnico.

---

## 17. Alertas

Las alertas son una salida fundamental del sistema.

Ejemplo:

> **Alerta preventiva**
>
> El Camino Rural 27 presenta riesgo crítico estimado para las 18:00.
>
> Última salida recomendada: **16:00**.
>
> Se recomienda evaluar el traslado preventivo de producción, ganado o maquinaria.

Para el MVP, la alerta puede mostrarse únicamente dentro de la aplicación.

Como evolución futura:

- notificaciones push;
- WhatsApp;
- SMS;
- correo electrónico.

---

## 18. Activación del análisis

El sistema no necesita esperar a que la lluvia comience.

El backend puede consultar periódicamente el pronóstico.

Ejemplo conceptual:

```text
Scheduler
    ↓
Consulta pronóstico
    ↓
¿Existe precipitación relevante?
    ↓
No → espera próxima actualización
Sí → ejecuta análisis de riesgo
```

Cuando existe un evento de interés:

1. actualiza datos dinámicos;
2. genera las features;
3. ejecuta el modelo;
4. calcula el riesgo futuro;
5. detecta la hora crítica;
6. calcula Última Ventana;
7. guarda resultados;
8. actualiza el mapa;
9. genera alertas cuando corresponde.

---

## 19. Frecuencia de actualización

Para el MVP, se puede ejecutar el análisis:

- cada hora; o
- cuando el pronóstico supera un umbral determinado.

No todos los datos deben actualizarse con la misma frecuencia.

### Datos prácticamente estáticos

- caminos;
- elevación;
- pendiente;
- geometría;
- características topográficas.

### Datos dinámicos

- pronóstico;
- lluvia acumulada;
- estado reciente del terreno;
- predicciones.

---

## 20. Caso de uso principal

### Escenario

Un productor necesita retirar ganado antes de una tormenta.

El establecimiento tiene una única ruta práctica de salida que atraviesa varios caminos rurales.

### Flujo

1. El sistema detecta una previsión de lluvias intensas.
2. Actualiza las condiciones meteorológicas.
3. Evalúa cada segmento de la ruta.
4. Proyecta el riesgo para las próximas horas.
5. Detecta que un tramo alcanzará riesgo crítico aproximadamente a las 18:00.
6. El recorrido completo requiere 1 hora y 20 minutos.
7. Se utiliza un margen preventivo de 40 minutos.
8. El sistema calcula:

```text
Última salida recomendada: 16:00
```

9. El productor recibe la alerta.
10. Puede decidir adelantar el traslado.

---

## 21. Historias de usuario

### HU-01 — Visualizar riesgo

**Como productor**, quiero visualizar los caminos cercanos a mi establecimiento según su nivel de riesgo para identificar rápidamente posibles problemas de acceso.

### HU-02 — Consultar camino

**Como productor**, quiero seleccionar un camino para conocer su riesgo actual y futuro.

### HU-03 — Conocer hora crítica

**Como productor**, quiero saber cuándo un camino podría alcanzar condiciones críticas para anticipar decisiones.

### HU-04 — Última salida

**Como productor**, quiero conocer hasta qué hora conviene iniciar un traslado para evitar quedar bloqueado durante el recorrido.

### HU-05 — Recibir alerta

**Como productor**, quiero recibir una alerta cuando una ruta relevante para mi establecimiento presente un riesgo elevado.

### HU-06 — Comprender la predicción

**Como usuario**, quiero conocer los principales factores asociados al riesgo para interpretar la recomendación.

---

## 22. Pantallas mínimas del MVP

### 22.1 Mapa principal

Debe mostrar:

- caminos;
- segmentos;
- colores según riesgo;
- establecimiento o punto de origen;
- hora de última actualización.

### 22.2 Panel de camino

Debe mostrar:

- nombre o identificador;
- nivel de riesgo;
- riesgo actual;
- evolución esperada;
- hora crítica;
- Última Ventana;
- factores principales.

### 22.3 Alertas

Listado simple:

```text
CRÍTICA — Camino 27
Última salida recomendada: 16:00

ALTA — Camino 14
Riesgo elevado previsto dentro de 8 h
```

---

## 23. Flujo de experiencia del usuario

```text
Usuario abre el sistema
        ↓
Ve mapa de caminos
        ↓
Identifica segmentos coloreados
        ↓
Selecciona un camino
        ↓
Consulta riesgo y evolución
        ↓
Ve hora crítica
        ↓
Ve Última Ventana
        ↓
Toma una decisión logística
```

La experiencia debe priorizar la decisión y no la complejidad técnica del modelo.

---

## 24. Ejemplo de respuesta del sistema

```text
CAMINO: Paso Martínez

Estado actual:
🟡 Riesgo moderado — 38%

Pronóstico:
16:00 → 49%
17:00 → 61%
18:00 → 73%
19:00 → 84%

Hora crítica estimada:
18:00

Tiempo de recorrido:
1 h 20 min

Margen preventivo:
40 min

ÚLTIMA SALIDA RECOMENDADA:
16:00

Motivos principales:
- alta precipitación prevista;
- acumulación de lluvia previa;
- tramo ubicado en zona baja;
- presencia reciente de agua en las proximidades.
```

---

## 25. Demo para el hackathon

La demo debe contar una historia simple.

### Inicio

Se muestra un establecimiento rural y sus caminos de salida.

### Evento

El sistema recibe un pronóstico de lluvia intensa.

### Análisis

Los caminos cambian progresivamente de nivel de riesgo.

Uno de los segmentos se vuelve el punto crítico de la ruta.

### Resultado

El sistema muestra:

> **Riesgo crítico previsto: 18:00**

y posteriormente:

> **Última salida recomendada: 16:00**

### Acción

El usuario entiende que todavía posee una ventana de aproximadamente dos horas para iniciar el traslado.

La demostración debe enfatizar que el valor no está en mostrar que va a llover, sino en **traducir la lluvia prevista en tiempo disponible para actuar**.

---

## 26. Diferencial

Muchas herramientas meteorológicas responden:

> ¿Va a llover?

Otros sistemas pueden responder:

> ¿Qué zonas tienen riesgo de inundación?

Última Ventana intenta responder:

> **¿Cuánto tiempo tengo para usar este camino antes de que el riesgo sea demasiado alto?**

El diferencial es transformar:

```text
Pronóstico
    ↓
Riesgo territorial
    ↓
Tiempo disponible
    ↓
Decisión logística
```

---

## 27. Evolución futura

Después del MVP, la plataforma podría incorporar:

- rutas alternativas automáticas;
- optimización logística;
- reportes de productores;
- estado real de transitabilidad;
- integración con municipios;
- alertas mediante WhatsApp;
- aplicaciones móviles;
- sensores de campo;
- modelos calibrados por región;
- gestión de flotas;
- cálculo de pérdidas evitadas;
- seguimiento de ganado;
- integración con aseguradoras;
- modelos de riesgo para múltiples tipos de vehículos.

---

## 28. Aprendizaje progresivo

Una evolución especialmente valiosa es permitir que usuarios u organismos reporten:

```text
✅ Transitable
⚠️ Complicado
❌ Intransitable
```

Estos reportes pueden transformarse en observaciones reales que permitan recalibrar o reentrenar los modelos.

El sistema podría evolucionar desde un MVP con datos limitados hacia un predictor entrenado con información específica de caminos rurales de Corrientes.

---

## 29. Limitaciones del MVP

El sistema debe presentarse como una herramienta de **estimación y apoyo a la decisión**.

No debe afirmar:

> “Este camino se cortará exactamente a las 18:00.”

La formulación adecuada es:

> **“El segmento podría alcanzar condiciones de riesgo crítico aproximadamente a las 18:00 según las condiciones y datos disponibles.”**

La Última Ventana es una recomendación preventiva y no una garantía absoluta de transitabilidad.

---

## 30. Métricas de éxito del MVP

En el hackathon, el éxito se puede evaluar principalmente por funcionamiento del sistema y claridad del caso de uso.

### Técnicas

- caminos correctamente georreferenciados;
- datos asociados a segmentos;
- generación automática de features;
- predicción ejecutable;
- resultados almacenados;
- visualización correcta en mapa;
- cálculo automático de Última Ventana.

### Producto

- el usuario entiende el riesgo;
- el usuario entiende qué tramo es crítico;
- el usuario sabe hasta cuándo debería actuar;
- la información es visualmente clara;
- la recomendación puede demostrarse en pocos minutos.

---

## 31. Criterios de aceptación del MVP

Se considera que el MVP cumple su objetivo si:

1. existe al menos una región rural cargada;
2. existen caminos divididos en segmentos;
3. cada segmento puede asociarse a información territorial y meteorológica;
4. el sistema puede generar un `risk_score`;
5. el sistema puede proyectar riesgo para diferentes horarios;
6. puede determinar una hora crítica;
7. puede calcular la Última Ventana;
8. el backend expone los resultados;
9. el frontend representa los caminos en un mapa;
10. el usuario puede consultar el detalle de un camino;
11. el sistema puede mostrar al menos una alerta preventiva;
12. la demo completa puede ejecutarse de principio a fin.

---

## 32. Definición resumida del producto

> **Última Ventana es una plataforma predictiva para caminos rurales que combina datos meteorológicos, satelitales y topográficos para estimar el riesgo de intransitabilidad y calcular hasta qué momento conviene realizar movimientos logísticos antes de que un tramo alcance condiciones críticas.**

---

## 33. Mensaje principal para el pitch

> **No te decimos solamente cuánto va a llover. Te decimos cuánto tiempo te queda para actuar.**
