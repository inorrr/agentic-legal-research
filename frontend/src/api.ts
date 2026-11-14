/** Local transport with explicit recovery; never replay an ambiguous failed write. */
export class ConnectionError extends Error {
  constructor() {
    super('The local app is not reachable. From the project directory, run python scripts/start_local.py and keep that terminal open, then choose Retry connection. Your entries are still here; check the refreshed history before repeating an action.');
    this.name = 'ConnectionError';
  }
}

interface ClientOptions {
  getToken: () => string;
  setToken: (token: string) => void;
  fetcher?: typeof fetch;
}

const EXPIRED_SESSION = 'Refresh the workspace to obtain a local session token';

export async function requestAPI<T>(url: string, method: string, body: unknown, options: ClientOptions, refreshed = false): Promise<T> {
  const fetcher = options.fetcher ?? fetch;
  let response: Response;
  try {
    response = await fetcher(url, {
      method,
      headers: { ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(method !== 'GET' ? { 'X-Workspace-Token': options.getToken() } : {}) },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    // A write may have completed before its response was lost. Do not replay it.
    throw new ConnectionError();
  }
  if (!response.ok) {
    let description = `Request failed (${response.status}).`;
    let detail: unknown;
    try {
      const data = await response.json(); detail = data.detail;
      if (typeof detail === 'string') description = detail;
      else if (Array.isArray(detail)) description = detail.map((item: { msg?: string }) => item.msg || 'Invalid input').join('; ');
    } catch { /* Use status message. */ }
    if ([502, 503, 504].includes(response.status) && detail === undefined) throw new ConnectionError();
    // This exact middleware response establishes that the handler never ran.
    // Refresh its token and retry once; other 403s and failed writes are not retried.
    if (response.status === 403 && detail === EXPIRED_SESSION && method !== 'GET' && !refreshed) {
      const bootstrap = await requestAPI<{ csrf_token: string }>('/api/bootstrap', 'GET', undefined, options, true);
      options.setToken(bootstrap.csrf_token);
      return requestAPI<T>(url, method, body, options, true);
    }
    throw new Error(description);
  }
  return response.status === 204 ? undefined as T : response.json();
}
