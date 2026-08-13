import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3000";
  const hostname = host.split(":")[0] ?? "";
  const isLocalAddress =
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname.startsWith("192.168.") ||
    hostname.startsWith("10.") ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname);
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (isLocalAddress ? "http" : "https");
  const base = new URL(`${protocol}://${host}`);
  const preview = new URL("/og.png", base).toString();

  return {
    metadataBase: base,
    title: "Carnes Luévanos · Sistema Administrativo",
    description: "PWA administrativa para ventas, inventario, compras, clientes, proveedores y operación de Carnes Luévanos.",
    manifest: "/manifest.webmanifest",
    applicationName: "Carnes Luévanos",
    appleWebApp: {
      capable: true,
      statusBarStyle: "black-translucent",
      title: "Carnes Luévanos",
    },
    icons: {
      icon: [
        { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
        { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
      ],
      shortcut: "/icon-192.png",
      apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
    },
    openGraph: {
      title: "Carnes Luévanos · Sistema Administrativo",
      description: "Controla tu negocio desde cualquier dispositivo.",
      type: "website",
      images: [{ url: preview, width: 1536, height: 1024, alt: "Carnes Luévanos Sistema Administrativo" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Carnes Luévanos · Sistema Administrativo",
      description: "Controla tu negocio desde cualquier dispositivo.",
      images: [preview],
    },
  };
}

export const viewport: Viewport = {
  themeColor: "#07111b",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
