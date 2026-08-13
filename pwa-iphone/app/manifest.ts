import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Carnes Luévanos · Sistema Administrativo",
    short_name: "Carnes Luévanos",
    description: "Ventas, inventario, compras, clientes, proveedores y operación desde iPhone.",
    start_url: "/",
    display: "standalone",
    background_color: "#08131f",
    theme_color: "#08131f",
    orientation: "portrait",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
