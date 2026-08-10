// DRF hands back errors in several shapes depending on where they're raised:
//   "just a string"                      (APIException with a str detail)
//   ["a list of strings"]                (top-level ValidationError with a str)
//   { detail: "..." }                    (permission / not-found)
//   { non_field_errors: ["..."] }        (serializer.validate())
//   { field: ["..."] | "..." }           (per-field validation)
// This flattens any of them to the first human-readable message.

export function firstError(
  data: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (Array.isArray(data)) {
    return typeof data[0] === "string" ? data[0] : fallback;
  }
  if (typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (typeof obj.detail === "string") return obj.detail;
    if (Array.isArray(obj.non_field_errors) && typeof obj.non_field_errors[0] === "string") {
      return obj.non_field_errors[0];
    }
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === "string") return value;
      if (Array.isArray(value) && typeof value[0] === "string") {
        return key === "non_field_errors" ? value[0] : `${key}: ${value[0]}`;
      }
    }
  }
  return fallback;
}
