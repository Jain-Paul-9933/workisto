import { forwardRef } from "react";

/**
 * The primitives, ported from the Claude Design "Foundations" file.
 *
 * Everything here reads semantic tokens (`bg-surface`, `text-muted`) rather
 * than ramp steps or `dark:` variants — the theme flip lives entirely in
 * globals.css, so a component never restates it. Controls are 48px tall,
 * comfortably over the 44px touch minimum, and the focus ring is global.
 */

const CONTROL =
  "min-h-12 w-full rounded-full border-[1.5px] bg-field px-4 text-base text-ink " +
  "outline-none transition placeholder:text-faint focus:border-accent";

// --- Button ----------------------------------------------------------------

const BUTTON_VARIANTS = {
  // Filled: the one action a screen most wants you to take.
  primary: "border-transparent bg-accent text-[var(--ui-accent-text)] hover:bg-[var(--ui-accent-hover)]",
  // Outlined: real actions that shouldn't compete with the primary one.
  secondary: "border-accent bg-transparent text-accent-ink hover:bg-accent-soft",
  // Outlined rather than filled on purpose — destructive actions should be
  // reachable without being the loudest thing on the screen.
  danger: "border-danger bg-transparent text-danger-ink hover:bg-danger-soft",
} as const;

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: keyof typeof BUTTON_VARIANTS;
    loading?: boolean;
  }
>(function Button(
  { className = "", variant = "primary", loading = false, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={
        "inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-full " +
        "border-[1.5px] px-6 text-base font-semibold transition " +
        "disabled:cursor-not-allowed disabled:opacity-45 " +
        BUTTON_VARIANTS[variant] +
        " " +
        className
      }
      {...props}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="size-4 animate-spin rounded-full border-2 border-current/40 border-t-current"
        />
      )}
      {children}
    </button>
  );
});

// --- Form controls ---------------------------------------------------------

export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }
>(function Input({ className = "", invalid, ...props }, ref) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={`${CONTROL} ${invalid ? "border-danger" : "border-field-border"} ${className}`}
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
      className={`${CONTROL} border-field-border px-3 ${className}`}
      {...props}
    />
  );
});

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className = "", ...props }, ref) {
  return (
    <textarea
      ref={ref}
      // The one control that isn't a pill — a multi-line box reads as a box.
      className={
        "w-full resize-y rounded-inner border-[1.5px] border-field-border bg-field px-4 py-3 " +
        "text-base text-ink outline-none transition placeholder:text-faint focus:border-accent " +
        className
      }
      {...props}
    />
  );
});

export function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="grid gap-1.5">
      <span className="text-sm font-semibold text-ink">{label}</span>
      {children}
      {hint && !error && <span className="text-caption text-muted">{hint}</span>}
      {error && (
        <span className="flex items-baseline gap-1.5 text-sm text-danger-ink">
          {/* The glyph is decorative; the message carries the meaning. */}
          <span aria-hidden="true">!</span>
          {error}
        </span>
      )}
    </label>
  );
}

export function ErrorText({ children }: { children: React.ReactNode }) {
  if (!children) return null;
  return (
    <p role="alert" className="flex items-baseline gap-1.5 text-sm text-danger-ink">
      <span aria-hidden="true">!</span>
      {children}
    </p>
  );
}

// --- Containers ------------------------------------------------------------

export function Card({
  className = "",
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={
        "rounded-card border border-divider bg-bg p-5 shadow-sm " + className
      }
    >
      {children}
    </div>
  );
}

const BADGE_TONES = {
  neutral: "bg-[var(--tone-neutral-bg)] text-[var(--tone-neutral-ink)]",
  green: "bg-[var(--tone-green-bg)] text-[var(--tone-green-ink)]",
  amber: "bg-[var(--tone-amber-bg)] text-[var(--tone-amber-ink)]",
  red: "bg-[var(--tone-red-bg)] text-[var(--tone-red-ink)]",
  indigo: "bg-[var(--tone-indigo-bg)] text-[var(--tone-indigo-ink)]",
} as const;

export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: keyof typeof BADGE_TONES;
}) {
  return (
    <span
      className={
        "inline-flex items-center whitespace-nowrap rounded-full px-3 py-1 " +
        "text-[13px] font-semibold " +
        BADGE_TONES[tone]
      }
    >
      {children}
    </span>
  );
}
