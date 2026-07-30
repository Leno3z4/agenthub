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

        <Link href="/login" className="landing-login">
          Login
        </Link>

        <Link href="/onboarding" className="landing-launch">
          Launch app
        </Link>
      </div>
    </nav>
  );
}
