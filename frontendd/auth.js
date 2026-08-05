import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Twitter from "next-auth/providers/twitter";

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
    Twitter({
      clientId: process.env.TWITTER_CLIENT_ID,
      clientSecret: process.env.TWITTER_CLIENT_SECRET,
      version: "2.0",
    }),
  ],

  session: { strategy: "jwt" },

  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.provider && profile) {
        const providerId = profile.sub ?? profile.id ?? profile.data?.id;
        if (!providerId) throw new Error("Provider did not return a user id");

        const res = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/users/register`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              provider: account.provider,
              provider_id: providerId,
              email: profile.email ?? null,
              name: profile.name ?? profile.username ?? null,
              picture: profile.picture ?? profile.image ?? null,
            }),
          },
        );

        if (!res.ok) {
          throw new Error(`Backend register failed: ${res.status} ${await res.text()}`);
        }

        const data = await res.json();
        token.userId = data.user_id;
      }

      return token;
    },

    async session({ session, token }) {
      if (session.user) {
        session.user = { ...session.user, id: token.userId };
      }
      return session;
    },
  },
});
