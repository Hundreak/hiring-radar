import {NextRequest, NextResponse} from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';

function buildTargetUrl(request: NextRequest, path: string[]): string {
  const search = request.nextUrl.search || '';
  return `${BACKEND_URL}/api/${path.join('/')}${search}`;
}

function buildProxyHeaders(request: NextRequest): Headers {
  const headers = new Headers(request.headers);

  headers.delete('host');
  headers.delete('connection');
  headers.delete('content-length');
  headers.delete('transfer-encoding');

  headers.set('x-forwarded-host', request.headers.get('host') ?? '127.0.0.1:3000');
  headers.set('x-forwarded-proto', request.nextUrl.protocol.replace(':', ''));

  return headers;
}

async function proxy(
  request: NextRequest,
  context: {params: Promise<{path: string[]}>}
) {
  const {path} = await context.params;
  const targetUrl = buildTargetUrl(request, path);
  const headers = buildProxyHeaders(request);

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: 'manual',
    cache: 'no-store',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.arrayBuffer();
  }

  let response: Response;

  try {
    response = await fetch(targetUrl, init);
  } catch (error) {
    const detail =
      error instanceof Error
        ? `Backend request failed: ${error.message}`
        : 'Backend request failed.';

    return NextResponse.json({detail}, {status: 502});
  }

  const responseHeaders = new Headers();

  for (const [key, value] of response.headers.entries()) {
    const lowerKey = key.toLowerCase();

    if (
      lowerKey === 'content-encoding' ||
      lowerKey === 'content-length' ||
      lowerKey === 'transfer-encoding'
    ) {
      continue;
    }

    if (lowerKey === 'set-cookie') {
      continue;
    }

    responseHeaders.append(key, value);
  }


  responseHeaders.set('cache-control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
  responseHeaders.set('pragma', 'no-cache');
  responseHeaders.set('expires', '0');

  const nextResponse = new NextResponse(response.body, {
    status: response.status,
    headers: responseHeaders,
  });

  const getSetCookie = (response.headers as Headers & {
    getSetCookie?: () => string[];
  }).getSetCookie;

  if (typeof getSetCookie === 'function') {
    for (const cookie of getSetCookie.call(response.headers)) {
      nextResponse.headers.append('set-cookie', cookie);
    }
  } else {
    const cookie = response.headers.get('set-cookie');
    if (cookie) {
      nextResponse.headers.append('set-cookie', cookie);
    }
  }

  return nextResponse;
}

export async function GET(
  request: NextRequest,
  context: {params: Promise<{path: string[]}>}
) {
  return proxy(request, context);
}

export async function POST(
  request: NextRequest,
  context: {params: Promise<{path: string[]}>}
) {
  return proxy(request, context);
}

export async function PUT(
  request: NextRequest,
  context: {params: Promise<{path: string[]}>}
) {
  return proxy(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: {params: Promise<{path: string[]}>}
) {
  return proxy(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: {params: Promise<{path: string[]}>}
) {
  return proxy(request, context);
}