/** In-memory sliding-window rate limit for /api/ai/* (guest abuse mitigation). */

const WINDOW_MS = 60_000;
const hits = new Map();

function clientIp(req) {
  return req.ip || req.socket?.remoteAddress || "unknown";
}

/**
 * @param {number} maxPerMinute 0 disables limiting
 */
export function createAiRateLimitMiddleware(maxPerMinute) {
  return function aiRateLimitMiddleware(req, res, next) {
    if (!maxPerMinute || maxPerMinute <= 0) return next();

    const ip = clientIp(req);
    const now = Date.now();
    let bucket = hits.get(ip);
    if (!bucket) {
      bucket = [];
      hits.set(ip, bucket);
    }
    while (bucket.length && bucket[0] < now - WINDOW_MS) {
      bucket.shift();
    }
    if (bucket.length >= maxPerMinute) {
      return res.status(429).json({
        success: false,
        message: "Too many AI requests; retry shortly."
      });
    }
    bucket.push(now);
    next();
  };
}
