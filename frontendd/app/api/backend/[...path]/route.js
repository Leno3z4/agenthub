import { getToken } from "next-auth/jwt";

export const dynamic = "force-dynamic";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-g0m8.onrender.com";

const METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"];

async function proxy(request, { params }) {
  const token = await getToken({
    req: request,
    secret: process.env.AUTH_SECRET,
  });

  if (!token?.userId) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const path = params.path?.join("/") || "";
  const target = new URL(`${BACKEND_URL.replace(/\/$/, "")}/${path}`);
  target.search = new URL(request.url).search;

  const incomingBody =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const headers = new Headers();
  const contentType = request.headers.get("content-type");

  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  headers.set("Authorization", `Bearer ${token.apiKey || ""}`);

  let response = await fetch(target, {
    method: request.method,
    headers,
    body: incomingBody,
    cache: "no-store",
  });

  /*
   * /wallet/link intentionally rotates the API key. The newly issued
   * key is placed in an HttpOnly cookie by that route, while the
   * existing Auth.js JWT still contains the pre-link key.
   *
   * If that old JWT key is rejected, retry once with the rotated
   * HttpOnly credential bound to the same user.
   */
  if (response.status === 401) {
    const cookie = request.cookies.get("__Host-alias_api_credential")?.value || "";
    const separator = cookie.indexOf(":");

    if (separator > 0) {
      const cookieUserId = decodeURIComponent(cookie.slice(0, separator));
      const cookieApiKey = decodeURIComponent(cookie.slice(separator + 1));

      if (cookieUserId === String(token.userId) && cookieApiKey) {
        response = await fetch(target, {
          method: request.method,
          headers: new Headers({
            ...(contentType ? { "Content-Type": contentType } : {}),
            Authorization: `Bearer ${cookieApiKey}`,
          }),
          body: incomingBody,
          cache: "no-store",
        });
      }
    }
  }

  const responseHeaders = new Headers();
  const responseContentType = response.headers.get("content-type");

  if (responseContentType) {
    responseHeaders.set("Content-Type", responseContentType);
  }

  return new Response(response.body, {
    status: response.status,
    headers: responseHeaders,
  });
}

export async function GET(request, context) {
  return proxy(request, context);
}

export async function POST(request, context) {
  return proxy(request, context);
}

export async function PUT(request, context) {
  return proxy(request, context);
}

export async function PATCH(request, context) {
  return proxy(request, context);
}

export async function DELETE(request, context) {
  return proxy(request, context);
}
