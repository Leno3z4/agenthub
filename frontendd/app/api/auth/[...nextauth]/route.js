import { auth } from "@/auth";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-g0m8.onrender.com";

export async function POST(request) {
  const session = await auth();

  if (!session?.user?.id || !session.user.authId) {
    return Response.json(
      { detail: "Unauthorized" },
      { status: 401 }
    );
  }

  const body = await request.json();

  if (!body.wallet_address) {
    return Response.json(
      { detail: "Wallet address is required." },
      { status: 400 }
    );
  }

  const response = await fetch(
    `${BACKEND_URL}/wallet/link`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Auth":
          process.env.BACKEND_INTERNAL_SECRET,
      },
      body: JSON.stringify({
        user_id: session.user.id,
        google_id: session.user.authId,
        email: session.user.email,
        name: session.user.name,
        picture: session.user.image ?? null,
        wallet_address: body.wallet_address,
      }),
    }
  );

  const text = await response.text();

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}
