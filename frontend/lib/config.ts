// Where the Django API lives, from the Next.js server's perspective.
// In Docker this is the `web` service; locally it's localhost:8000.
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
