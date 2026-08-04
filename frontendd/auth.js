import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Twitter from "next-auth/providers/twitter";

export const {
  handlers,
  signIn,
  signOut,
  auth,
} = NextAuth({
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

  session: {
    strategy: "jwt",
  },

  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.provider === "google") {
       
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/users/register`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              google_id: profile.sub,
              email: profile.email,
              name: profile.name,
              picture: profile.picture,
            }),
          }
        );

        if (!res.ok) {
          throw new Error("Failed to register backend user");
        }

        const data = await res.json();

        token.userId = data.user_id;
      }

      return token;
    },

    async session({ session, token }) {
      session.user.id = token.userId;
      return session;
    },
  },
});
