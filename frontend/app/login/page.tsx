import { bffBaseUrl } from "@/lib/config";

export default function LoginPage() {
  return (
    <main>
      <section className="hero stack">
        <h1>Log in</h1>
        <p>Start the Auth0 login flow through the FastAPI BFF.</p>
        <p>
          <a href={`${bffBaseUrl}/auth/login`}>Continue to Auth0 via the BFF</a>
        </p>
      </section>
    </main>
  );
}
