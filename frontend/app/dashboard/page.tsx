import Link from "next/link";

import { createOrderAction, logoutAction } from "@/app/dashboard/actions";
import { getCurrentUser, getOrders } from "@/lib/bff";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams?: Promise<{ error?: string }>;
}) {
  const params = searchParams ? await searchParams : undefined;
  const me = await getCurrentUser();
  const orders = me ? await getOrders() : [];

  return (
    <main>
      <section className="hero stack">
        <h1>Dashboard</h1>
        <p>This page loads the current user from the BFF and uses the BFF proxy for sample downstream requests.</p>
      </section>

      {!me ? (
        <section className="card stack">
          <p>You are not logged in.</p>
          <p>
            <Link href="/login">Go to login</Link>
          </p>
        </section>
      ) : (
        <section className="card-grid">
          <article className="card">
            <h2>Current user</h2>
            <p><strong>Name:</strong> {me.user.name ?? "Unknown"}</p>
            <p><strong>Email:</strong> {me.user.email ?? "Unavailable"}</p>
            <p><strong>Subject:</strong> {me.user.id}</p>
            <p><strong>Roles:</strong> {me.user.roles.length > 0 ? me.user.roles.join(", ") : "None"}</p>
            <form action={logoutAction}>
              <input type="hidden" name="csrfToken" value={me.csrfToken} />
              <button type="submit">Log out</button>
            </form>
          </article>

          <article className="card">
            <h2>Sample service data</h2>
            <p>This form submits to a Next.js server action, which forwards the session cookies and `X-CSRF-Token` header to the BFF.</p>
            <form className="stack" action={createOrderAction}>
              <input type="hidden" name="csrfToken" value={me.csrfToken} />
              <label>
                Item
                <input name="item" defaultValue="Sample order" minLength={1} maxLength={100} required />
              </label>
              <label>
                Quantity
                <input name="quantity" type="number" min={1} max={1000} defaultValue={1} required />
              </label>
              <button type="submit">Create order via BFF</button>
            </form>

            <ul className="stack order-list">
              {orders.map((order) => (
                <li key={order.id}>
                  <strong>#{order.id}</strong> {order.item} × {order.quantity} <em>({order.created_by})</em>
                </li>
              ))}
              {orders.length === 0 ? <li>No sample orders yet.</li> : null}
            </ul>
          </article>

          {params?.error ? (
            <article className="card error-card">
              <h2>Request error</h2>
              <p>{params.error}</p>
            </article>
          ) : null}
        </section>
      )}
    </main>
  );
}
