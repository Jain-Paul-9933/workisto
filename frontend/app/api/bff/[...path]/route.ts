import { NextRequest } from "next/server";

import { proxy } from "@/lib/bff";

// One catch-all that proxies every /api/bff/* call to Django /api/*.
// e.g. POST /api/bff/auth/login/  ->  POST {BACKEND}/api/auth/login/
async function handler(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  const segments = (path ?? []).filter(Boolean).join("/");
  const search = req.nextUrl.search;
  return proxy(req, `/api/${segments}/${search}`);
}

export {
  handler as GET,
  handler as POST,
  handler as PUT,
  handler as PATCH,
  handler as DELETE,
};
