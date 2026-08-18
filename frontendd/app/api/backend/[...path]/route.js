import { getToken } from "next-auth/jwt";

export const dynamic = "force-dynamic";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-g0m8.onrender.com";

const AUTH_COOKIE =
  process.env.NODE_ENV === "production"
    ? "__Secure-authjs.session-token"
    : "authjs.session-token";

async function getAuthToken(request) {
  const secret = process.env.AUTH_SECRET;

  if (!secret) {
    throw new Error("AUTH_SECRET is not configured.");
  }

  let token = await getToken({
    req: request,
    secret,
    secureCookie: process.env.NODE_ENV === "production",
    cookieName: AUTH_COOKIE,
  });

  if (!token?.userId) {
    token = await getToken({
      req: request,
      secret,
      secureCookie: process.env.NODE_ENV !== "production",
      cookieName:
        process.env.NODE_ENV === "production"
          ? "authjs.session-token"
          : "__Secure-authjs.session-token",
    });
  }

  return token;
}

function getApiKey(request, token) {
  // Current rotated credential.
  const credentialCookie = request.cookies.get(
    "__Host-alias_api_credential"
  )?.value;

  if (credentialCookie) {
    const separator = credentialCookie.indexOf(":");

    if (separator > 0) {
      const userId = decodeURIComponent(
        credentialCookie.slice(0, separator)
      );

      const apiKey = decodeURIComponent(
        credentialCookie.slice(separator + 1)
      );

      if (
        String(userId) === String(token?.userId) &&
        apiKey
      ) {
        return apiKey;
      }
    }
  }

  // Fall back to the API key stored in the Auth.js token.
  return token?.apiKey || null;
}
function isApiKeyRegenerationPath(path) {
  return /^users\/[^/]+\/api-key\/regenerate$/.test(path);
}
async function proxy(request, context) {
  const token = await getAuthToken(request);

  if (!token?.userId) {
    return Response.json(
      { detail: "Unauthorized" },
      { status: 401 }
    );
  }

  const path = context.params?.path?.join("/") || "";

  const regenerationPath =
    request.method === "POST" &&
    isApiKeyRegenerationPath(path);

  const apiKey = getApiKey(request, token);

  if (!apiKey && !regenerationPath) {
    return Response.json(
      { detail: "Unauthorized" },
      { status: 401 }
    );
  }

  const target = new URL(
    `${BACKEND_URL.replace(/\/$/, "")}/${path}`
  );

  target.search = new URL(request.url).search;

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const headers = new Headers();

  const contentType = request.headers.get("content-type");

  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  if (apiKey) {
    headers.set("Authorization", `Bearer ${apiKey}`);
  }
  if (regenerationPath) {
    headers.set("X-Alias-User-Id", String(token.userId));
  }
  const response = await fetch(target, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
  });

  const responseHeaders = new Headers();

  const responseContentType =
    response.headers.get("content-type");

  if (responseContentType) {
    responseHeaders.set(
      "Content-Type",
      responseContentType
    );
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
