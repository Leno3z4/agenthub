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

  session: {
    strategy: "jwt",
  },

  callbacks: {
   async jwt({ token, account, profile }) {
      if (account?.provider === "google") {
       
        console.log("BACKEND:", process.env.NEXT_PUBLIC_BACKEND_URL);
        console.log("PROFILE:", profile);
        
        const url = `${process.env.NEXT_PUBLIC_BACKEND_URL}/users/register`;
        
        console.log("REGISTER URL:", url);
        
        const res = await fetch(url, {
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
          const text = await res.text();
          console.error("Backend register failed:", res.status, text);
          throw new Error(text);
        }

        console.log("STATUS:", res.status);
        
        const body = await res.text();
        
        console.log("BODY:", body);
        
        if (!res.ok) {
          throw new Error(body);
        }
        
        const data = JSON.parse(body);

        token.userId = data.user_id;
        token.userId = profile.sub;
      }

    
      return token;
    }

    async session({ session, token }) {
      if (session.user) {
        session.user = {
          ...session.user,
          id: token.userId,
        };
      }
    
      return session;
    },
  },
});
