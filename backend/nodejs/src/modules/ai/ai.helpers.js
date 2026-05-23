import { resolveRequestTrace } from "../../utils.js";

/** @param {import("express").Request} req */
export function traceHeadersOrFallback(req) {
  return req.traceHeaders ?? resolveRequestTrace(req.headers).traceHeaders;
}
