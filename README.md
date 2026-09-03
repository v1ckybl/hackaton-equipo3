# Última Ventana

Plataforma predictiva para estimar el riesgo de intransitabilidad de caminos
rurales y calcular la última ventana segura de salida.

## Base de datos en Supabase

El esquema PostgreSQL/PostGIS persiste los cruces geoespaciales, los snapshots
de features utilizados por el modelo y la trazabilidad de training e inferencia.
El proyecto remoto configurado es `lepivdjhmuzlinfhxsyr`.

Las migraciones versionadas viven en `supabase/migrations/`. El schema de la
aplicación es privado (`ultima_ventana`): FastAPI se conecta por PostgreSQL y no
se expone mediante la Data API de Supabase.

Preparación:

```powershell
npm install
Copy-Item .env.example .env
# Completar DATABASE_URL y SUPABASE_DB_PASSWORD localmente.
npx supabase login
npm run supabase:link
```

Validación y despliegue seguro:

```powershell
npm run db:preflight
npm run db:push:dry
npm run db:push
npm run db:lint
npm run db:check
npm run db:test
```

`db:test` ejecuta datos de prueba dentro de una transacción y finaliza con
`ROLLBACK`. Nunca se debe ejecutar `supabase db reset --linked` contra este
proyecto.

Documentación: [docs/05_ESQUEMA_BASE_DATOS.md](docs/05_ESQUEMA_BASE_DATOS.md).

## Machine Learning sintético en Google Colab

El flujo ML se ejecuta íntegramente en Google Colab y genera sus propios datos.
No consulta datasets, APIs, Supabase ni Google Drive. La red se usa solamente
para clonar este repositorio e instalar las dependencias declaradas.

| Notebook | Uso | Abrir |
| --- | --- | --- |
| `00_pipeline_sintetico_colab.ipynb` | Pipeline completo recomendado | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/v1ckybl/hackaton-equipo3/blob/feature/ultima-ventana/notebooks/00_pipeline_sintetico_colab.ipynb) |
| `01_generacion_eda_sintetica.ipynb` | Generación, validación y EDA | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/v1ckybl/hackaton-equipo3/blob/feature/ultima-ventana/notebooks/01_generacion_eda_sintetica.ipynb) |
| `02_entrenamiento_evaluacion_inferencia.ipynb` | Entrenamiento, métricas e inferencia | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/v1ckybl/hackaton-equipo3/blob/feature/ultima-ventana/notebooks/02_entrenamiento_evaluacion_inferencia.ipynb) |

Cada notebook funciona con **Run all** desde un runtime nuevo. La configuración
está concentrada en su primera celda de código y usa por defecto la rama
`feature/ultima-ventana`, 10.000 filas, semilla `42` y CPU. Los resultados quedan
en `/content/ultima_ventana_outputs/` y pueden empaquetarse como ZIP; la descarga
automática está desactivada por defecto.

El pipeline mantiene una única implementación reusable en
`ultima_ventana_ml/`. Además de exportar el modelo y sus metadatos, prueba una
predicción individual, inferencia batch, una serie horaria controlada y el
cálculo demostrativo de la última salida.

### Artefactos

- dataset CSV sintético y manifest con SHA-256;
- modelo XGBoost `model.json` y schema de features;
- métricas contra baseline trivial y heurístico;
- metadata reproducible y model card;
- predicciones batch y temporales de demostración.

> El modelo produce un índice experimental entrenado con features y labels
> completamente sintéticos. Sus métricas no representan precisión validada
> sobre caminos reales ni deben usarse para decisiones operativas.

Los scripts `scripts/generate_synthetic_v1.py` y
`scripts/train_synthetic_v1.py` se conservan como entradas de automatización,
pero los notebooks son la interfaz soportada para ejecutar el flujo.
