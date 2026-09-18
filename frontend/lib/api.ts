export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/backend${path}`, {
    ...init,
    headers: { ...init?.headers },
    cache: "no-store",
    credentials: "same-origin",
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      message = (await response.json()).detail ?? message;
    } catch {
      // Use the HTTP status fallback when the backend did not return JSON.
    }
    throw new Error(message);
  }

  return response.json();
}

