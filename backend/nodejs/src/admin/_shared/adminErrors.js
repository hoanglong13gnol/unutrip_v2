/** Admin route error text — hide upstream/DB details in production. */

export function adminErrorMessage(error, fallback = "Internal server error") {
  if (process.env.NODE_ENV === "production") return fallback;
  return error?.message || fallback;
}

export function adminHtmlErrorMessage(error, fallback = "Admin error") {
  return `Admin Error: ${adminErrorMessage(error, fallback)}`;
}
