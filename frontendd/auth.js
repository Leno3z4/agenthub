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
  trustHost: true,
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    Twitter({
      clientId: process.env.TWITTER_CLIENT_ID,
      clientSecret: process.env.TWITTER_CLIENT_SECRET,
      version: "2.0",
      authorization: {
        url: "https://twitter.com/i/oauth2/authorize",
        params: {
          scope: "users.read tweet.read offline.access",
        },
      },
    }),
  ],

  session: {
    strategy: "jwt",
  },

  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.provider === "google" || account?.provider === "twitter") {
        const url = `${process.env.NEXT_PUBLIC_BACKEND_URL}/users/register`;
        const isTwitter = account.provider === "twitter";
        const twitterProfile = isTwitter ? profile?.data : undefined;
        const identityId = isTwitter ? twitterProfile?.id : profile?.sub;
        const email = profile?.email || null;
        const name = isTwitter
          ? twitterProfile?.name || twitterProfile?.username
          : profile?.name;
        const picture = isTwitter
          ? twitterProfile?.profile_image_url
          : profile?.picture;

        if (!identityId) {
          throw new Error("Missing OAuth account ID");
        }

        if (!name) {
          throw new Error("Missing required OAuth profile name");
        }

        const res = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Internal-Auth": process.env.BACKEND_INTERNAL_SECRET,
          },
          body: JSON.stringify({
            google_id: isTwitter ? null : identityId,
            x_id: isTwitter ? identityId : null,
            provider: account.provider,
            email,
            name,
            picture,
          }),
        });

        if (!res.ok) {
          throw new Error(await res.text());
        }

        const data = await res.json();

        token.userId = data.user_id;
        token.apiKey = data.api_key || undefined;
        token.authId = identityId;
        token.provider = account.provider;
      }

      return token;
    },

    async session({ session, token }) {
      if (session.user) {
        session.user = {
          ...session.user,
          id: token.userId,
          authId: token.authId,
          provider: token.provider,
        };
      }

      return session;
    },
  },
});
