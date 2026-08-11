// Where the Django API lives, from the Next.js server's perspective.
// In Docker this is the `web` service; locally it's localhost:8000.
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

// The FastAPI read service (increment 11). The BFF calls it server-side with a
// short-lived token Django mints (ADR 0001); the browser never reaches it.
export const SEARCH_URL = process.env.SEARCH_URL ?? "http://localhost:8001";
