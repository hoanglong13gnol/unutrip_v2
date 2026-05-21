import { db } from "../db.js";

function getRunner(conn) {
  if (!conn) return null;
  return {
    query(sql, params) {
      return conn.execute(sql, params);
    }
  };
}

export async function listReviewsByDestinationId(destinationId) {
  return db.query(
    `
      SELECT r.id, r.user_id, u.full_name as user_name, u.avatar as user_avatar,
             r.destination_id, r.rating, r.comment, r.images_json, r.created_at
      FROM reviews r
      JOIN users u ON u.id = r.user_id
      WHERE r.destination_id = ?
      ORDER BY r.created_at DESC, r.id DESC
    `,
    [destinationId]
  );
}

export async function destinationExists(destinationId, conn) {
  const runner = getRunner(conn);
  if (runner) {
    const [rows] = await runner.query("SELECT id FROM app_places WHERE id = ? LIMIT 1", [destinationId]);
    return rows.length > 0;
  }
  const row = await db.get("SELECT id FROM app_places WHERE id = ?", [destinationId]);
  return !!row;
}

export async function insertReview({ userId, destinationId, rating, comment, imagesJson }, conn) {
  const runner = getRunner(conn);
  if (runner) {
    const [result] = await runner.query(
      "INSERT INTO reviews (user_id, destination_id, rating, comment, images_json) VALUES (?, ?, ?, ?, ?)",
      [userId, destinationId, rating, comment, imagesJson]
    );
    return { lastInsertRowid: result.insertId };
  }
  return db.run(
    "INSERT INTO reviews (user_id, destination_id, rating, comment, images_json) VALUES (?, ?, ?, ?, ?)",
    [userId, destinationId, rating, comment, imagesJson]
  );
}

export async function getReviewAggregateByDestinationId(destinationId, conn) {
  const runner = getRunner(conn);
  if (runner) {
    const [rows] = await runner.query(
      "SELECT AVG(rating) as avg, COUNT(*) as cnt FROM reviews WHERE destination_id = ?",
      [destinationId]
    );
    return rows[0];
  }
  return db.get("SELECT AVG(rating) as avg, COUNT(*) as cnt FROM reviews WHERE destination_id = ?", [
    destinationId
  ]);
}

export async function updateDestinationReviewAggregate({ destinationId, rating, reviewCount }, conn) {
  const runner = getRunner(conn);
  if (runner) {
    await runner.query("UPDATE app_places SET rating = ?, review_count = ? WHERE id = ?", [
      rating,
      reviewCount,
      destinationId
    ]);
    return;
  }
  await db.run("UPDATE app_places SET rating = ?, review_count = ? WHERE id = ?", [
    rating,
    reviewCount,
    destinationId
  ]);
}

const ADMIN_REVIEW_SELECT = `
  SELECT r.id, r.user_id, r.destination_id, r.rating, r.comment, r.images_json, r.created_at,
         u.full_name AS user_name, u.email AS user_email,
         p.name AS place_name
  FROM reviews r
  JOIN users u ON u.id = r.user_id
  JOIN app_places p ON p.id = r.destination_id
`;

export async function listAdminReviews() {
  return db.query(`${ADMIN_REVIEW_SELECT} ORDER BY r.created_at DESC, r.id DESC LIMIT 500`);
}

export async function searchAdminReviews({ like }) {
  return db.query(
    `
      ${ADMIN_REVIEW_SELECT}
      WHERE CAST(r.id AS CHAR) LIKE ?
         OR u.full_name LIKE ?
         OR u.email LIKE ?
         OR p.name LIKE ?
         OR r.comment LIKE ?
         OR CAST(r.rating AS CHAR) LIKE ?
      ORDER BY r.created_at DESC, r.id DESC
      LIMIT 500
    `,
    [like, like, like, like, like, like]
  );
}

export async function getAdminReviewById(id) {
  return db.get(`${ADMIN_REVIEW_SELECT} WHERE r.id = ? LIMIT 1`, [id]);
}

export async function deleteReviewById(id, conn) {
  const runner = getRunner(conn);
  const selectSql = "SELECT id, destination_id FROM reviews WHERE id = ? LIMIT 1";
  let row;
  if (runner) {
    const [rows] = await runner.query(selectSql, [id]);
    row = rows[0];
  } else {
    row = await db.get(selectSql, [id]);
  }
  if (!row) return null;

  if (runner) {
    await runner.query("DELETE FROM reviews WHERE id = ?", [id]);
  } else {
    await db.run("DELETE FROM reviews WHERE id = ?", [id]);
  }
  return row.destination_id;
}

export async function adminUpdateReview({ id, rating, comment }, conn) {
  const runner = getRunner(conn);
  const selectSql = "SELECT id, destination_id FROM reviews WHERE id = ? LIMIT 1";
  let row;
  if (runner) {
    const [rows] = await runner.query(selectSql, [id]);
    row = rows[0];
  } else {
    row = await db.get(selectSql, [id]);
  }
  if (!row) return null;

  if (runner) {
    await runner.query("UPDATE reviews SET rating = ?, comment = ? WHERE id = ?", [rating, comment, id]);
  } else {
    await db.run("UPDATE reviews SET rating = ?, comment = ? WHERE id = ?", [rating, comment, id]);
  }
  return row.destination_id;
}

export async function recalculateDestinationReviewAggregate(destinationId, conn) {
  const agg = await getReviewAggregateByDestinationId(destinationId, conn);
  await updateDestinationReviewAggregate(
    {
      destinationId,
      rating: Number(agg.avg ?? 0),
      reviewCount: Number(agg.cnt ?? 0)
    },
    conn
  );
}
