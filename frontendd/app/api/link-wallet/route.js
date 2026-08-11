import { auth } from "@/auth";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-g0m8.onrender.com";

export async function POST(request) {
  const session = await auth();

  if (!session?.user?.id || !session.user.authId) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();

  if (
    !body.wallet_address ||
    !/^0x[a-fA-F0-9]{40}$/.test(body.wallet_address)
  ) {
    return Response.json(
      { detail: "Valid wallet address is required." },
      { status: 400 }
    );
  }

  const response = await fetch(`${BACKEND_URL}/wallet/link`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Auth": process.env.BACKEND_INTERNAL_SECRET,
    },
    body: JSON.stringify({
      user_id: session.user.id,
      google_id: session.user.authId,
      email: session.user.email,
      name: session.user.name,
      picture: session.user.image ?? null,
      wallet_address: body.wallet_address,
    }),
  });

  const text = await response.text();

  if (!response.ok) {
    return new Response(text, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    return Response.json(
      { detail: "Backend returned invalid JSON." },
      { status: 502 }
    );
  }

  if (!data.api_key || !data.agent_address) {
    return Response.json(
      { detail: "Wallet linking returned incomplete credentials." },
      { status: 502 }
    );
  }

  /*
   * The rotated backend API key never enters the browser's JavaScript
   * environment. It is stored in an HttpOnly, Secure, SameSite cookie.
   *
   * Bind it to the authenticated user so the proxy cannot accidentally
   * use a previous account's credential after an account switch.
   */
  const credential = [
    encodeURIComponent(String(session.user.id)),
    encodeURIComponent(data.api_key),
  ].join(":");

  const result = Response.json({
    agent_address: data.agent_address,
    wallet_connected: true,
  });

  result.headers.append(
    "Set-Cookie",
    `__Host-alias_api_credential=${credential}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000`
  );

  return result;
}
