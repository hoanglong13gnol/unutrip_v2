import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

import { assertSafeProductionConfig } from "./config/env.js";
import { createApp } from "./app.js";
import { pool } from "./db.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.BACKEND_PORT || process.env.PORT || 3000);
const HOST = process.env.BACKEND_HOST || process.env.HOST || "0.0.0.0";

async function main() {
  try {
    assertSafeProductionConfig();
    const app = createApp();

    const publicImagesDir = path.join(__dirname, "..", "public", "images");

    const server = app.listen(PORT, HOST, () => {
      console.log(`SmartTravel backend running on http://${HOST}:${PORT}`);
      console.log(`Admin Dashboard: http://${HOST}:${PORT}/admin/dashboard`);
      if (fs.existsSync(publicImagesDir)) {
        console.log(`Serving destination images from: ${publicImagesDir}`);
      }
    });

    const shutdown = (signal) => {
      console.log(`[shutdown] ${signal}, closing HTTP server and DB pool…`);
      server.close((closeErr) => {
        if (closeErr) {
          console.error("[shutdown] server.close:", closeErr);
        }
        pool
          .end()
          .then(() => {
            process.exit(closeErr ? 1 : 0);
          })
          .catch((e) => {
            console.error("[shutdown] pool.end:", e);
            process.exit(1);
          });
      });
      setTimeout(() => {
        console.error("[shutdown] forced exit after timeout");
        process.exit(1);
      }, 10_000).unref();
    };

    process.once("SIGTERM", () => shutdown("SIGTERM"));
    process.once("SIGINT", () => shutdown("SIGINT"));
  } catch (error) {
    console.error("Failed to start server:", error);
    process.exit(1);
  }
}

main();
