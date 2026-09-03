# Última Ventana

Plataforma predictiva para estimar el riesgo de intransitabilidad de caminos
rurales y calcular la última ventana segura de salida.

## Base de datos

El esquema PostgreSQL/PostGIS persiste los cruces geoespaciales, los snapshots
de features utilizados por el modelo y la trazabilidad de training e inferencia.

Documentación: [docs/05_ESQUEMA_BASE_DATOS.md](docs/05_ESQUEMA_BASE_DATOS.md).

Inicio local:

```powershell
Copy-Item .env.example .env
docker compose up -d
docker compose exec -T db psql -U ultima_ventana -d ultima_ventana -f /workspace/db/tests/smoke.sql
```

Los scripts de `db/init/` se ejecutan automáticamente al crear por primera vez
el volumen de PostgreSQL.
