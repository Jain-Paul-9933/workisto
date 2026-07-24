"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiSend, setRoleCookie } from "@/lib/api-client";
import { Button, ErrorText, Field, Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await apiSend("/auth/login", "POST", { email, password });
    setLoading(false);
    if (!res.ok) {
      setError("Invalid email or password.");
      return;
    }
    const user = await res.json();
    setRoleCookie(user.role);
    router.replace(user.role === "PROVIDER" ? "/dashboard" : "/search");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
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
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </Field>
      <ErrorText>{error}</ErrorText>
      <Button type="submit" disabled={loading}>
        {loading ? "Signing in…" : "Sign in"}
      </Button>
      <p className="text-center text-sm text-neutral-500">
        New here?{" "}
        <Link href="/register" className="font-medium text-indigo-600 hover:underline">
          Create an account
        </Link>
      </p>
    </form>
  );
}
