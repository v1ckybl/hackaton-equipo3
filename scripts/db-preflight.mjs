import { safeDatabaseTarget, withDatabase } from "./lib/database.mjs";

const managedVersions = ["20260903120000", "20260903121000"];

try {
  await withDatabase(async (client, connectionString) => {
    console.log(`Preflight remoto: ${safeDatabaseTarget(connectionString)}`);

    const postgisResult = await client.query(`
      SELECT namespace.nspname AS extension_schema
      FROM pg_extension AS extension
      JOIN pg_namespace AS namespace ON namespace.oid = extension.extnamespace
      WHERE extension.extname = 'postgis'
    `);

    if (postgisResult.rowCount === 1) {
      const extensionSchema = postgisResult.rows[0].extension_schema;
      if (!["extensions", "public"].includes(extensionSchema)) {
        throw new Error(
          `PostGIS ya existe en el schema ${extensionSchema}; hay que adaptar el search_path antes de desplegar.`,
        );
      }
      console.log(`PostGIS existente: schema ${extensionSchema}`);
    } else {
      console.log("PostGIS no existe todavia; la primera migracion lo habilitara.");
    }

    const objectsResult = await client.query(`
      SELECT
        EXISTS (
          SELECT 1 FROM pg_namespace WHERE nspname = 'ultima_ventana'
        ) AS schema_exists,
        (
          SELECT count(*)::integer
          FROM pg_class AS relation
          JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'ultima_ventana'
            AND relation.relkind IN ('r', 'p', 'v', 'm', 'S')
        ) AS object_count
    `);

    const migrationTableResult = await client.query(`
      SELECT to_regclass('supabase_migrations.schema_migrations') IS NOT NULL AS exists
    `);

    let appliedVersions = [];
    if (migrationTableResult.rows[0].exists) {
      const migrationsResult = await client.query(
        `SELECT version FROM supabase_migrations.schema_migrations WHERE version = ANY($1::text[])`,
        [managedVersions],
      );
      appliedVersions = migrationsResult.rows.map(({ version }) => version);
    }

    const { schema_exists: schemaExists, object_count: objectCount } = objectsResult.rows[0];
    if (schemaExists && objectCount > 0 && appliedVersions.length === 0) {
      throw new Error(
        "El schema ultima_ventana ya contiene objetos pero no registra estas migraciones. Se cancela para no pisar datos remotos.",
      );
    }

    console.log(
      `Schema remoto: ${schemaExists ? `${objectCount} objetos` : "aun no creado"}; migraciones propias aplicadas: ${appliedVersions.length}/${managedVersions.length}.`,
    );
    console.log("Preflight: OK");
  });
} catch (error) {
  console.error(`Preflight: ERROR - ${error.message}`);
  process.exitCode = 1;
}
