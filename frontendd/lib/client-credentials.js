/*
 * Compatibility helper for older dashboard code.
 *
 * Alias API credentials are no longer stored in localStorage or exposed
 * through the client session. Keep this helper only so older callers can
 * continue asking for a user id while the API layer handles credentials
 * server-side.
 */
export function getStoredCredentials(session) {
  if (typeof window !== "undefined") {
    localStorage.removeItem("alias_api_key");
  }

  return {
    userId: session?.user?.id || "",
    apiKey: "",
  };
}
