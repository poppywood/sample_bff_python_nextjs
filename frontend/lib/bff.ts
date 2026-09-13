import "server-only";

import { cookies } from "next/headers";

import { bffBaseUrl } from "@/lib/config";

type CurrentUser = {
  id: string;
  email: string | null;
  name: string | null;
  picture: string | null;
  roles: string[];
};

export type MeResponse = {
  user: CurrentUser;
  csrfToken: string;
};

export type Order = {
  id: number;
  item: string;
  quantity: number;
  created_by: string;
};

async function getCookieHeader() {
  const cookieStore = await cookies();
  return cookieStore.toString();
}

export async function getCurrentUser(): Promise<MeResponse | null> {
  const response = await fetch(`${bffBaseUrl}/me`, {
    headers: {
      cookie: await getCookieHeader(),
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to load the current user from the BFF.");
  }

  return (await response.json()) as MeResponse;
}

export async function getOrders(): Promise<Order[]> {
  const response = await fetch(`${bffBaseUrl}/api/service-a/orders`, {
    headers: {
      cookie: await getCookieHeader(),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load sample data from the BFF.");
  }

  return (await response.json()) as Order[];
}

export async function createOrder(input: { item: string; quantity: number; csrfToken: string }) {
  const response = await fetch(`${bffBaseUrl}/api/service-a/orders`, {
    method: "POST",
    headers: {
      cookie: await getCookieHeader(),
      "content-type": "application/json",
      "x-csrf-token": input.csrfToken,
    },
    body: JSON.stringify({
      item: input.item,
      quantity: input.quantity,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await response.text() || "Failed to create sample data through the BFF.");
  }
}

export async function logout(csrfToken: string) {
  const response = await fetch(`${bffBaseUrl}/auth/logout`, {
    method: "POST",
    headers: {
      cookie: await getCookieHeader(),
      "x-csrf-token": csrfToken,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to log out through the BFF.");
  }

  return (await response.json()) as { logout_url: string };
}
