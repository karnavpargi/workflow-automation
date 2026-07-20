/**
 * Thin fetch wrapper for the Django REST API.
 *
 * - Attaches ``Authorization: Bearer <access>`` when a token is in memory.
 * - Attaches ``X-Tenant-Slug`` for every tenant-scoped call.
 * - Returns parsed JSON, or throws an :class:`ApiError` on non-2xx.
 */

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export interface ApiClientOptions {
  getAccessToken: () => string | null;
  getTenantSlug: () => string | null;
  baseUrl?: string;
}

export class ApiClient {
  private getAccessToken: () => string | null;
  private getTenantSlug: () => string | null;
  private baseUrl: string;

  constructor(opts: ApiClientOptions) {
    this.getAccessToken = opts.getAccessToken;
    this.getTenantSlug = opts.getTenantSlug;
    this.baseUrl = opts.baseUrl ?? "";
  }

  private headers(extra: Record<string, string> = {}): Record<string, string> {
    const h: Record<string, string> = { "Content-Type": "application/json", ...extra };
    const tok = this.getAccessToken();
    if (tok) h["Authorization"] = `Bearer ${tok}`;
    const slug = this.getTenantSlug();
    if (slug) h["X-Tenant-Slug"] = slug;
    return h;
  }

  async request<T>(
    method: string,
    path: string,
    body?: unknown,
    extraHeaders: Record<string, string> = {}
  ): Promise<T> {
    const res = await fetch(this.baseUrl + path, {
      method,
      headers: this.headers(extraHeaders),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: "include",
    });
    const ct = res.headers.get("content-type") ?? "";
    const data: unknown = ct.includes("application/json") ? await res.json() : await res.text();
    if (!res.ok) {
      throw new ApiError(`HTTP ${res.status} on ${method} ${path}`, res.status, data);
    }
    return data as T;
  }

  get<T>(path: string) {
    return this.request<T>("GET", path);
  }
  post<T>(path: string, body?: unknown) {
    return this.request<T>("POST", path, body);
  }
  del<T>(path: string) {
    return this.request<T>("DELETE", path);
  }
}
