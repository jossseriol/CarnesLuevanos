import { NextRequest, NextResponse } from "next/server";

const ALLOWED_LOCAL_HOSTS = /^(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)$/;

type RouteContext = {
  params: Promise<{ path?: string[] }>;
};

async function forward(request: NextRequest, context: RouteContext) {
  const targetBase = request.headers.get("x-carnes-api-url")?.replace(/\/$/, "");
  if (!targetBase) {
    return NextResponse.json({ detail: "Servidor API no configurado" }, { status: 400 });
  }

  let targetUrl: URL;
  try {
    targetUrl = new URL(targetBase);
  } catch {
    return NextResponse.json({ detail: "Servidor API inválido" }, { status: 400 });
  }

  if (targetUrl.protocol !== "http:" || !ALLOWED_LOCAL_HOSTS.test(targetUrl.hostname)) {
    return NextResponse.json({ detail: "Solo se permite proxy a la API local" }, { status: 400 });
  }

  const params = await context.params;
  const path = params.path?.join("/") ?? "";
  const search = new URL(request.url).search;
  const upstreamUrl = `${targetUrl.origin}/${path}${search}`;
  const apiKey = request.headers.get("x-api-key");
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();

  const upstream = await fetch(upstreamUrl, {
    method: request.method,
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": request.headers.get("content-type") ?? "application/json" } : {}),
      ...(apiKey ? { "x-api-key": apiKey } : {}),
    },
    body,
    cache: "no-store",
  });

  const contentType = upstream.headers.get("content-type") ?? "application/json";
  const responseBody = await upstream.text();
  return new NextResponse(responseBody, {
    status: upstream.status,
    headers: {
      "Content-Type": contentType,
      "Cache-Control": "no-store",
    },
  });
}

export {
  forward as GET,
  forward as POST,
  forward as PUT,
  forward as PATCH,
  forward as DELETE,
};
