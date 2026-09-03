import pg from "pg";

const { Client } = pg;

export function getDatabaseUrl() {
  const value = process.env.DATABASE_URL?.trim();

  if (!value || value.includes("[YOUR-")) {
    throw new Error(
      "Falta DATABASE_URL. Copia .env.example a .env y pega la URI Session pooler de Supabase.",
    );
  }

  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("DATABASE_URL no es una URI PostgreSQL valida.");
  }

  if (!["postgresql:", "postgres:"].includes(parsed.protocol)) {
    throw new Error("DATABASE_URL debe usar el protocolo postgresql://.");
  }

  if (parsed.searchParams.get("sslmode") !== "require") {
    throw new Error("DATABASE_URL debe incluir sslmode=require.");
  }

  return value;
}

export function safeDatabaseTarget(connectionString) {
  const parsed = new URL(connectionString);
  return `${parsed.hostname}:${parsed.port || "5432"}/${parsed.pathname.slice(1) || "postgres"}`;
}

export async function connectDatabase() {
  const connectionString = getDatabaseUrl();
  const client = new Client({
    connectionString,
    connectionTimeoutMillis: 10_000,
    query_timeout: 30_000,
    application_name: "ultima-ventana-db-tools",
  });

  await client.connect();
  return { client, connectionString };
}

export async function withDatabase(callback) {
  const { client, connectionString } = await connectDatabase();
  try {
    return await callback(client, connectionString);
  } finally {
    await client.end();
  }
}
