import OnboardingForm from "@/components/provider/onboarding-form";
import { Card } from "@/components/ui";
import { serverGet } from "@/lib/server-api";
import type { Provider } from "@/lib/types";

// Doubles as onboarding (no profile yet) and profile editing (already onboarded)
// — the form switches between POST /providers/ and PATCH /providers/me/.
export default async function OnboardingPage() {
  const res = await serverGet("/api/providers/me/");
  const provider: Provider | null = res.ok ? await res.json() : null;

  return (
    <div className="mx-auto max-w-xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">
          {provider ? "Edit your profile" : "Set up your provider profile"}
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          {provider
            ? "Update your details and service area."
            : "Tell customers who you are and where you work. You can change this anytime."}
        </p>
      </div>
      <Card>
        <OnboardingForm initial={provider} />
      </Card>
    </div>
  );
}
