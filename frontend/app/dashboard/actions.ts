"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createOrder, logout } from "@/lib/bff";

function getText(formData: FormData, key: string) {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

export async function createOrderAction(formData: FormData) {
  const item = getText(formData, "item");
  const quantity = Number(getText(formData, "quantity"));
  const csrfToken = getText(formData, "csrfToken");

  if (!item || !csrfToken || Number.isNaN(quantity) || quantity < 1 || quantity > 1000) {
    redirect("/dashboard?error=Please+provide+a+valid+item+and+quantity.");
  }

  try {
    await createOrder({ item, quantity, csrfToken });
  } catch {
    redirect("/dashboard?error=The+BFF+could+not+create+the+sample+order.");
  }

  revalidatePath("/dashboard");
  redirect("/dashboard");
}

export async function logoutAction(formData: FormData) {
  const csrfToken = getText(formData, "csrfToken");

  if (!csrfToken) {
    redirect("/dashboard?error=The+BFF+could+not+complete+logout.");
  }

  let logoutUrl = "";

  try {
    const { logout_url } = await logout(csrfToken);
    logoutUrl = logout_url;
  } catch {
    redirect("/dashboard?error=The+BFF+could+not+complete+logout.");
  }

  redirect(logoutUrl);
}
