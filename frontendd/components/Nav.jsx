import Link from "next/link";

export default function Nav() {
  return (
    <nav className="landing-nav">
      <Link href="/" className="landing-logo">
        ALIAS
      </Link>

      <div className="landing-nav-right">
        <a href="#system" className="landing-nav-link">
          Infrastructure
        </a>

        <Link href="/onboarding" className="landing-login">
          Login
        </Link>

        <Link href="/onboarding" className="landing-launch">
          Launch app
        </Link>
      </div>

      <style jsx>{`
        .landing-nav {
          width: 100%;
          max-width: 1400px;
          margin-left: auto;
          margin-right: auto;
          padding-left: 40px;
          padding-right: 40px;
        }

        .landing-nav-right {
          margin-left: auto;
          flex: 0 0 auto;
        }

        .landing-nav-link,
        .landing-login,
        .landing-launch {
          flex-shrink: 0;
          white-space: nowrap;
        }

        @media (max-width: 800px) {
          .landing-nav {
            width: 100%;
            max-width: none;
            padding-left: 20px;
            padding-right: 20px;
          }
        }

        @media (max-width: 560px) {
          .landing-nav {
            width: 100vw;
            max-width: 100vw;
            margin-left: 0;
            margin-right: 0;
            padding-left: 20px;
            padding-right: 20px;
          }

          .landing-nav-right {
            margin-left: auto;
            gap: 14px;
          }

          .landing-login {
            display: none;
          }

          .landing-launch {
            min-width: 112px;
            height: 39px;
            padding-left: 15px;
            padding-right: 15px;
          }
        }
      `}</style>
    </nav>
  );
}
