import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "https://agenthub-wine.vercel.app";

export const {
  handlers,
  signIn,
  signOut,
  auth,
} = NextAuth({
  secret: process.env.AUTH_SECRET,
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
  ],

  session: {
    strategy: "jwt",
  },

  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.provider === "google") {
        if (!account.id_token) {
          throw new Error("Google ID token was not provided");
        }

        const res = await fetch(`${BACKEND_URL}/users/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            provider: "google",
            id_token: account.id_token,
          }),
        });

        if (!res.ok) {
          throw new Error(`Backend register failed: ${res.status} ${await res.text()}`);
        }

        const data = await res.json();
        token.userId = data.user_id;
        token.googleIdToken = account.id_token;
      }

      return token;
    },

    async session({ session, token }) {
      if (session.user) {
        session.user = {
          ...session.user,
          id: token.userId,
          googleIdToken: token.googleIdToken,
        };
      }

      return session;
    },
  },
});
