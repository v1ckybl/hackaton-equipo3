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
