export const runtime = "nodejs";

const RPC_URL = "https://rpc.testnet.arc.io";
const MAX_REQUEST_BODY_BYTES = readPositiveInteger(
  process.env.RPC_MAX_BODY_BYTES,
  64 * 1024,
);
const RATE_LIMIT_WINDOW_MS = readPositiveInteger(
  process.env.RPC_RATE_LIMIT_WINDOW_MS,
  60 * 1000,
);
const RATE_LIMIT_MAX_REQUESTS = readPositiveInteger(
  process.env.RPC_RATE_LIMIT_MAX_REQUESTS,
  120,
);

// Keep this list intentionally narrow. These are the read, fee, and receipt
// methods used by wagmi/viem for the frontend's Arc wallet and deposit flow.
const ALLOWED_METHODS = new Set([
  "eth_chainId",
  "eth_blockNumber",
  "eth_call",
  "eth_estimateGas",
  "eth_feeHistory",
  "eth_gasPrice",
  "eth_getBalance",
  "eth_getBlockByHash",
  "eth_getBlockByNumber",
  "eth_getCode",
  "eth_getLogs",
  "eth_getStorageAt",
  "eth_getTransactionByHash",
  "eth_getTransactionCount",
  "eth_getTransactionReceipt",
  "net_version",
]);

// This is process-local, so it protects each running Next.js instance. Keep
// the limit conservative even when the app is deployed with multiple nodes.
const rateLimitBuckets = new Map();

function readPositiveInteger(value, fallback) {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function clientKey(req) {
  const forwarded = req.headers.get("x-forwarded-for");
  const address =
    forwarded?.split(",", 1)[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "unknown";

  return address.slice(0, 128);
}

function logRejected(req, reason, details = {}) {
  console.warn(
    JSON.stringify({
      event: "rpc_request_rejected",
      reason,
      client: clientKey(req),
      ...details,
    }),
  );
}

function rateLimited(req) {
  const now = Date.now();
  const key = clientKey(req);
  const bucket = rateLimitBuckets.get(key);

  if (!bucket || bucket.resetAt <= now) {
    rateLimitBuckets.set(key, {
      count: 1,
      resetAt: now + RATE_LIMIT_WINDOW_MS,
    });
    return false;
  }

  bucket.count += 1;
  return bucket.count > RATE_LIMIT_MAX_REQUESTS;
}

function pruneRateLimitBuckets() {
  const now = Date.now();
  for (const [key, bucket] of rateLimitBuckets) {
    if (bucket.resetAt <= now) {
      rateLimitBuckets.delete(key);
    }
  }
}

async function readBodyWithLimit(req) {
  const declaredLength = Number.parseInt(
    req.headers.get("content-length") || "",
    10,
  );

  if (Number.isInteger(declaredLength) && declaredLength > MAX_REQUEST_BODY_BYTES) {
    throw new Error("request body too large");
  }

  if (!req.body) {
    return "";
  }

  const reader = req.body.getReader();
  const chunks = [];
  let totalBytes = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      totalBytes += value.byteLength;
      if (totalBytes > MAX_REQUEST_BODY_BYTES) {
        await reader.cancel();
        throw new Error("request body too large");
      }

      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const body = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }

  return new TextDecoder().decode(body);
}

function jsonResponse(payload, status) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    },
  });
}

function getRpcRequests(payload) {
  if (Array.isArray(payload)) {
    return payload.length > 0 ? payload : null;
  }

  return payload && typeof payload === "object" ? [payload] : null;
}

export async function POST(req) {
  pruneRateLimitBuckets();

  if (rateLimited(req)) {
    logRejected(req, "rate_limit_exceeded");
    return jsonResponse({ error: "Too many requests." }, 429);
  }

  const contentType = req.headers.get("content-type") || "";
  if (!contentType.toLowerCase().startsWith("application/json")) {
    logRejected(req, "unsupported_content_type", { contentType });
    return jsonResponse({ error: "Content-Type must be application/json." }, 415);
  }

  let body;
  try {
    body = await readBodyWithLimit(req);
  } catch {
    logRejected(req, "request_body_too_large");
    return jsonResponse({ error: "Request body is too large." }, 413);
  }

  let payload;
  try {
    payload = JSON.parse(body);
  } catch {
    logRejected(req, "invalid_json");
    return jsonResponse({ error: "Invalid JSON." }, 400);
  }

  const rpcRequests = getRpcRequests(payload);
  if (!rpcRequests) {
    logRejected(req, "invalid_json_rpc_payload");
    return jsonResponse({ error: "A JSON-RPC request or batch is required." }, 400);
  }

  const methods = rpcRequests.map((request) => request?.method);
  const invalidMethod = methods.find(
    (method) => typeof method !== "string" || !ALLOWED_METHODS.has(method),
  );

  if (invalidMethod !== undefined) {
    logRejected(req, "method_not_allowed", {
      method:
        typeof invalidMethod === "string"
          ? invalidMethod.slice(0, 128)
          : "missing_or_invalid",
    });
    return jsonResponse({ error: "JSON-RPC method is not allowed." }, 403);
  }

  try {
    const upstream = await fetch(RPC_URL, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body,
      cache: "no-store",
    });
    const data = await upstream.text();

    return new Response(data, {
      status: upstream.status,
      headers: {
        "Content-Type":
          upstream.headers.get("content-type") || "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    console.error("RPC upstream request failed", error);
    return jsonResponse({ error: "RPC upstream unavailable." }, 502);
  }
}
