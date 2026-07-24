export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4 dark:bg-neutral-950">
      <div className="w-full max-w-sm space-y-6 rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
        <div className="space-y-1 text-center">
          <h1 className="text-2xl font-semibold text-indigo-600">Workisto</h1>
          <p className="text-sm text-neutral-500">Local services, booked in minutes.</p>
        </div>
        {children}
      </div>
    </div>
  );
}
