import mysql from "mysql2/promise";

import { DB_POOL_CONNECTION_LIMIT } from "./config/env.js";

const isProduction = process.env.NODE_ENV === "production";

const selectedDatabase = process.env.DB_NAME || "unudata";

if (selectedDatabase !== "unudata") {
  console.warn(
    `[DB_ENV] DB_NAME=${selectedDatabase} (expected unudata for production parity). Set DB_NAME in .env if this is intentional.`
  );
}

const dbConfig = {
  host: process.env.DB_HOST || "127.0.0.1",
  port: Number(process.env.DB_PORT || 3306),
  user: process.env.DB_USER || "root",
  password: process.env.DB_PASSWORD || "",
  database: selectedDatabase,
  waitForConnections: true,
  connectionLimit: DB_POOL_CONNECTION_LIMIT,
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0
};

if (isProduction) {
  console.log("[DB] MySQL pool ready (database=%s, limit=%d)", dbConfig.database, dbConfig.connectionLimit);
} else {
  console.log(
    "[DB] pool database=%s host=%s:%s user=%s limit=%d",
    dbConfig.database,
    dbConfig.host,
    dbConfig.port,
    dbConfig.user,
    dbConfig.connectionLimit
  );
}

export const pool = mysql.createPool(dbConfig);

export const db = {
  pool,

  query: async (sql, params) => {
    const [results] = await pool.execute(sql, params);
    return results;
  },

  get: async (sql, params) => {
    const [results] = await pool.execute(sql, params);
    return results[0];
  },

  run: async (sql, params) => {
    const [results] = await pool.execute(sql, params);
    return {
      lastInsertRowid: results.insertId,
      changes: results.affectedRows
    };
  }
};

export async function migrate() {
  console.log("[DB] migrate() skipped. Production schema is managed by MySQL dump/import scripts.");
}

export function jsonOrNull(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "object") return value;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}
