import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <section className="hero stack">
        <h1>Browser-facing FastAPI BFF starter</h1>
        <p>
          This sample shows a Next.js App Router frontend that authenticates through a FastAPI BFF,
          keeps browser session state in Redis, and reaches downstream services only through the BFF.
        </p>
        <nav className="nav-links">
          <Link href="/login">Log in with Auth0</Link>
          <Link href="/dashboard">Open dashboard</Link>
        </nav>
      </section>

      <section className="card stack">
        <h2>What this starter demonstrates</h2>
        <ul>
          <li>Auth0 login handled by FastAPI/Authlib.</li>
          <li>Redis-backed session cookies with a CSRF token for mutating requests.</li>
          <li>Short-lived internal RS256 JWTs minted by the BFF for downstream APIs.</li>
          <li>Two downstream demo flows that create orders and notes through the BFF only.</li>
        </ul>
      </section>
    </main>
  );
}
