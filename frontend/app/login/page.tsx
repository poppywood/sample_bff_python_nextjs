import { bffBaseUrl } from "@/lib/config";

export default function LoginPage() {
  return (
    <main>
      <section className="hero stack">
        <h1>Log in</h1>
        <p id="login-help">Start the Auth0 login flow through the FastAPI BFF on <code>{bffBaseUrl}</code>.</p>
        <p>
          <a href={`${bffBaseUrl}/auth/login`} aria-describedby="login-help">
            Continue to Auth0 via the BFF at {bffBaseUrl}
          </a>
        </p>
      </section>
    </main>
  );
}
