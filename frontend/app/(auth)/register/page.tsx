"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiSend, setRoleCookie } from "@/lib/api-client";
import { Button, ErrorText, Field, Input, Select } from "@/components/ui";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"CUSTOMER" | "PROVIDER">("CUSTOMER");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await apiSend("/auth/register", "POST", { email, password, role });
    setLoading(false);
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      // Surface the first field error Django/DRF returns.
      const firstError =
        data?.email?.[0] ?? data?.password?.[0] ?? data?.detail ??
        "Could not create your account.";
      setError(firstError);
      return;
    }
    const user = await res.json();
    setRoleCookie(user.role);
    router.replace(user.role === "PROVIDER" ? "/dashboard" : "/search");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Field label="I want to">
        <Select value={role} onChange={(e) => setRole(e.target.value as typeof role)}>
          <option value="CUSTOMER">Book services (customer)</option>
          <option value="PROVIDER">Offer services (provider)</option>
        </Select>
      </Field>
      <Field label="Email">
        <Input
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Field>
      <Field label="Password">
        <Input
          type="password"
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </Field>
      <ErrorText>{error}</ErrorText>
      <Button type="submit" disabled={loading}>
        {loading ? "Creating account…" : "Create account"}
      </Button>
      <p className="text-center text-sm text-neutral-500">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-indigo-600 hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
