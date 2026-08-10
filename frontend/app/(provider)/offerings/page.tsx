import { redirect } from "next/navigation";

import OfferingsManager from "@/components/provider/offerings-manager";
import { serverGet } from "@/lib/server-api";
import type { Category, Offering } from "@/lib/types";

export default async function OfferingsPage() {
  // Can't price services before there's a profile to hang them on.
  const meRes = await serverGet("/api/providers/me/");
  if (meRes.status === 404) redirect("/onboarding");

  const [offeringsRes, categoriesRes] = await Promise.all([
    serverGet("/api/providers/me/offerings/"),
    serverGet("/api/categories/"),
  ]);
  const offerings: Offering[] = offeringsRes.ok ? await offeringsRes.json() : [];
  const categories: Category[] = categoriesRes.ok ? await categoriesRes.json() : [];

  return <OfferingsManager initialOfferings={offerings} categories={categories} />;
}
