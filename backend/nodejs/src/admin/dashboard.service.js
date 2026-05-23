import { db } from "../db.js";

export async function fetchDashboardStats() {
  return db.get(`
    SELECT
      (SELECT COUNT(*) FROM users) as totalUsers,
      (SELECT COUNT(*) FROM app_places) as totalDestinations,
      (SELECT COUNT(*) FROM itineraries) as totalItineraries
  `);
}

export async function fetchLatestUsers(limit = 5) {
  return db.query(
    `
    SELECT full_name, email, created_at
    FROM users
    ORDER BY created_at DESC
    LIMIT ?
  `,
    [limit]
  );
}
