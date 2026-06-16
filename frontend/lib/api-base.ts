/**
 * API base URL for browser requests.
 * When unset, uses same-origin paths proxied by Next.js rewrites (see next.config.ts).
 */
export function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, "");
  return "";
}
