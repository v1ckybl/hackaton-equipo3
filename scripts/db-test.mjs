import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { safeDatabaseTarget, withDatabase } from "./lib/database.mjs";

const sqlPath = fileURLToPath(new URL("../db/tests/smoke.sql", import.meta.url));

try {
  const sql = await readFile(sqlPath, "utf8");
  await withDatabase(async (client, connectionString) => {
    console.log(`Smoke test transaccional: ${safeDatabaseTarget(connectionString)}`);
    await client.query(sql);
    console.log("Smoke test transaccional: OK (datos revertidos)");
  });
} catch (error) {
  console.error(`Smoke test transaccional: ERROR - ${error.message}`);
  process.exitCode = 1;
}
