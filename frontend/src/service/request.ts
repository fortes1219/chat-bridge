import axios, { type AxiosRequestConfig, type Method } from 'axios';
import { normalizeHttpError } from '@/service/error';

export interface RequestConfig<TData = unknown, TParams = unknown> {
  url: string;
  method: Method;
  headers?: AxiosRequestConfig<TData>['headers'];
  params?: TParams;
  data?: TData;
  signal?: AbortSignal;
  responseType?: AxiosRequestConfig<TData>['responseType'];
  timeout?: number;
}

/** A JSON call that takes longer than this has failed; the chat stream sets its own. */
const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * The page's one transport, same origin as the service.
 *
 * - It only sends and normalises rejected responses; it keeps no state and touches no store,
 *   router or view.
 * - It creates no AbortController; callers pass TanStack Query's `signal`, or their own, through.
 * - A 2xx body is checked against its schema by the API function, not here.
 * - The fetch adapter returns a response body as it arrives, so the chat stream uses this same
 *   instance with `responseType: 'stream'`.
 */
const http = axios.create({
  adapter: 'fetch',
  timeout: DEFAULT_TIMEOUT_MS
});

/** A refused stream request carries its error body as a stream; read it so it can be checked. */
async function withReadBody(error: unknown): Promise<unknown> {
  if (!axios.isAxiosError(error) || !(error.response?.data instanceof ReadableStream)) {
    return error;
  }
  const text = await new Response(error.response.data).text();
  try {
    error.response.data = JSON.parse(text);
  } catch {
    error.response.data = text;
  }
  return error;
}

http.interceptors.response.use(
  response => response,
  async (error: unknown) => Promise.reject(normalizeHttpError(await withReadBody(error)))
);

export async function request<TResponse, TData = unknown, TParams = unknown>(
  config: RequestConfig<TData, TParams>
): Promise<TResponse> {
  const response = await http.request<TResponse>({
    ...config
  });
  return response.data;
}
