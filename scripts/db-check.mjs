import { safeDatabaseTarget, withDatabase } from "./lib/database.mjs";

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

try {
  await withDatabase(async (client, connectionString) => {
    console.log(`Chequeo remoto: ${safeDatabaseTarget(connectionString)}`);

    const inventoryResult = await client.query(`
      SELECT
        count(*) FILTER (WHERE relation.relkind IN ('r', 'p'))::integer AS tables,
        count(*) FILTER (WHERE relation.relkind = 'v')::integer AS views
      FROM pg_class AS relation
      JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
      WHERE namespace.nspname = 'ultima_ventana'
    `);
    const inventory = inventoryResult.rows[0];
    assert(inventory.tables === 16, `Se esperaban 16 tablas y hay ${inventory.tables}.`);
    assert(inventory.views === 2, `Se esperaban 2 vistas y hay ${inventory.views}.`);

    const postgisResult = await client.query(`
      SELECT namespace.nspname AS extension_schema
      FROM pg_extension AS extension
      JOIN pg_namespace AS namespace ON namespace.oid = extension.extnamespace
      WHERE extension.extname = 'postgis'
    `);
    assert(postgisResult.rowCount === 1, "La extension PostGIS no esta instalada.");
    assert(
      ["extensions", "public"].includes(postgisResult.rows[0].extension_schema),
      `PostGIS esta en un schema inesperado: ${postgisResult.rows[0].extension_schema}.`,
    );

    const contractResult = await client.query(`
      SELECT version
      FROM ultima_ventana.feature_schema_versions
      WHERE is_active
      ORDER BY version
    `);
    assert(
      contractResult.rowCount === 1 && contractResult.rows[0].version === "v1",
      "Debe existir exactamente un contrato activo y debe ser v1.",
    );

    const exposureResult = await client.query(`
      WITH forbidden_roles AS (
        SELECT oid, rolname
        FROM pg_roles
        WHERE rolname IN ('anon', 'authenticated', 'service_role')
        UNION ALL
        SELECT 0::oid, 'PUBLIC'
      ), exposed AS (
        SELECT 'schema'::text AS object_type, namespace.nspname AS object_name,
               role.rolname AS grantee, acl.privilege_type
        FROM pg_namespace AS namespace
        CROSS JOIN LATERAL aclexplode(
          COALESCE(namespace.nspacl, acldefault('n', namespace.nspowner))
        ) AS acl
        JOIN forbidden_roles AS role ON role.oid = acl.grantee
        WHERE namespace.nspname = 'ultima_ventana'

        UNION ALL

        SELECT CASE WHEN relation.relkind = 'S' THEN 'sequence' ELSE 'relation' END,
               relation.relname, role.rolname, acl.privilege_type
        FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        CROSS JOIN LATERAL aclexplode(
          COALESCE(
            relation.relacl,
            acldefault(CASE WHEN relation.relkind = 'S' THEN 'S'::"char" ELSE 'r'::"char" END, relation.relowner)
          )
        ) AS acl
        JOIN forbidden_roles AS role ON role.oid = acl.grantee
        WHERE namespace.nspname = 'ultima_ventana'
          AND relation.relkind IN ('r', 'p', 'v', 'm', 'S')

        UNION ALL

        SELECT 'function', procedure.proname, role.rolname, acl.privilege_type
        FROM pg_proc AS procedure
        JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
        CROSS JOIN LATERAL aclexplode(
          COALESCE(procedure.proacl, acldefault('f', procedure.proowner))
        ) AS acl
        JOIN forbidden_roles AS role ON role.oid = acl.grantee
        WHERE namespace.nspname = 'ultima_ventana'
      )
      SELECT object_type, object_name, grantee, privilege_type
      FROM exposed
      ORDER BY object_type, object_name, grantee, privilege_type
    `);
    assert(
      exposureResult.rowCount === 0,
      `Hay ${exposureResult.rowCount} permisos no deseados para roles de la Data API.`,
    );

    console.log(
      `Inventario: ${inventory.tables} tablas, ${inventory.views} vistas, contrato v1 activo, PostGIS en ${postgisResult.rows[0].extension_schema}.`,
    );
    console.log("Seguridad: schema privado para anon/authenticated/service_role/PUBLIC.");
    console.log("Chequeo remoto: OK");
  });
} catch (error) {
  console.error(`Chequeo remoto: ERROR - ${error.message}`);
  process.exitCode = 1;
}
