import { forwardRef } from "react";

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(function Button({ className = "", ...props }, ref) {
  return (
    <button
      ref={ref}
      className={
        "w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-medium text-white " +
        "transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60 " +
        className
      }
      {...props}
    />
  );
});

export function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
        {label}
      </span>
      {children}
    </label>
  );
}

export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(function Input({ className = "", ...props }, ref) {
  return (
    <input
      ref={ref}
      className={
        "w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-neutral-900 " +
        "outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 " +
        "dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 " +
        className
      }
      {...props}
    />
  );
});

export const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(function Select({ className = "", ...props }, ref) {
  return (
    <select
      ref={ref}
      className={
        "w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-neutral-900 " +
        "outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 " +
        "dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 " +
        className
      }
      {...props}
    />
  );
});

export function ErrorText({ children }: { children: React.ReactNode }) {
  if (!children) return null;
  return <p className="text-sm text-red-600">{children}</p>;
}
