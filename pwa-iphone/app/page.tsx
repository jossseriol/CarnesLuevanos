"use client";

import { FormEvent, PointerEvent as ReactPointerEvent, useEffect, useRef, useState } from "react";

type Tab = "inicio" | "reportes" | "jelox" | "bandeja" | "usuarios" | "administrar";
type ModuleKey =
  | "ventas"
  | "compras"
  | "inventario"
  | "clientes"
  | "proveedores"
  | "pedidos"
  | "prestamos"
  | "nominas"
  | "rendimiento"
  | "informacion"
  | "empacadora"
  | "configuracion";

type RecordItem = {
  id: number;
  title: string;
  subtitle: string;
  amount?: number;
  status?: string;
  stock?: number;
  price?: number;
  date?: string;
  image?: string;
  client?: string;
  product?: string;
  time?: string;
  invoice?: string | number;
};

type ChartPeriod = "Hoy" | "7 días" | "30 días";
type ChartPoint = { label: string; detail: string; value: number; operations: number };

type ApiConnection = { url: string; key: string };
type AdminPermissionKey =
  | "ventas"
  | "inventario"
  | "clientes"
  | "pedidos"
  | "proveedores"
  | "compras"
  | "rendimiento"
  | "informacion"
  | "configuracion";
type AdminUser = {
  id: number;
  username: string;
  name: string;
  role: string;
  status: string;
  branch?: string;
  employeeNumber?: string;
  lastAccess?: string;
  permissions: Record<AdminPermissionKey, boolean>;
};
type CommercialInfo = {
  name: string;
  legalName: string;
  taxId: string;
  phone: string;
  email: string;
  address: string;
  currency: string;
};
type AdminPayload = { users: AdminUser[]; company: CommercialInfo };
type AuthDetail = {
  message?: string;
  mfa_setup_required?: boolean;
  mfa_required?: boolean;
  secret?: string;
  user_id?: number;
  admin_unlock_required?: boolean;
  locked_username?: string;
  failed_attempts?: number;
  remaining_attempts?: number;
};
type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: { results: ArrayLike<{ 0: { transcript: string } }> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};
type VoiceWindow = Window & {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
};
type LoginStep = "credentials" | "mfa" | "setup";

const LEGACY_ACTIVE_SESSION_KEY = "carnes-active-session";
const ACTIVE_SESSION_KEY = "carnes-active-session-v3";
const ADMIN_ONLY_RESET_KEY = "carnes-admin-only-reset-20260801-v2";
const PENDING_MFA_FLOW_KEY = "carnes-pending-mfa-flow-v1";
const PENDING_MFA_FLOW_TTL_MS = 5 * 60 * 1000;
const LOCAL_API_PROXY_PREFIX = "/api/local-proxy";

type PendingMfaFlow = {
  step: Exclude<LoginStep, "credentials">;
  user: string;
  password: string;
  mfaSetup: { secret: string; userId: number } | null;
  savedAt: number;
};

function readPendingMfaFlow(): PendingMfaFlow | null {
  if (typeof window === "undefined") return null;
  sessionStorage.removeItem(PENDING_MFA_FLOW_KEY);
  return null;
}

class ApiResponseError extends Error {
  status: number;
  detail: string | AuthDetail;

  constructor(status: number, detail: string | AuthDetail) {
    const message = typeof detail === "string" ? detail : detail.message ?? "No se pudo completar";
    super(message);
    this.name = "ApiResponseError";
    this.status = status;
    this.detail = detail;
  }
}

const moduleInfo: Record<ModuleKey, { title: string; subtitle: string; icon: string }> = {
  ventas: { title: "Ventas", subtitle: "Gestiona tus ventas", icon: "⌑" },
  compras: { title: "Compras", subtitle: "Gestiona tus compras", icon: "▢" },
  inventario: { title: "Inventario", subtitle: "Control de stock", icon: "◇" },
  clientes: { title: "Clientes", subtitle: "Gestión de clientes", icon: "◎" },
  proveedores: { title: "Proveedores", subtitle: "Registro de proveedores", icon: "▤" },
  pedidos: { title: "Pedidos", subtitle: "Pedidos a proveedores", icon: "▧" },
  prestamos: { title: "Préstamos y abonos", subtitle: "Créditos y pagos", icon: "$" },
  nominas: { title: "Nóminas", subtitle: "Gestión de nómina", icon: "♙" },
  rendimiento: { title: "Rendimiento", subtitle: "Reportes y KPIs", icon: "↗" },
  informacion: { title: "Información", subtitle: "Datos de la empresa", icon: "ⓘ" },
  empacadora: { title: "Empacadora", subtitle: "Operación y lotes", icon: "▦" },
  configuracion: { title: "Configuración", subtitle: "Usuarios y seguridad", icon: "⚙" },
};

const seed: Record<ModuleKey, RecordItem[]> = {
  ventas: [
    { id: 45, title: "#V-000145", subtitle: "Juan Pérez · 10:30", amount: 1250, status: "Pagado" },
    { id: 44, title: "#V-000144", subtitle: "María López · 09:15", amount: 890, status: "Pagado" },
    { id: 43, title: "#V-000143", subtitle: "Cliente General · 08:45", amount: 2150, status: "Pagado" },
    { id: 42, title: "#V-000142", subtitle: "Luis Gómez · 07:30", amount: 560, status: "Pagado" },
  ],
  compras: [
    { id: 78, title: "Carnes del Norte", subtitle: "15 may. 2024", amount: 4230, status: "Recibido" },
    { id: 77, title: "Distribuidora La Central", subtitle: "14 may. 2024", amount: 2980, status: "Recibido" },
    { id: 76, title: "Abastos Selectos", subtitle: "13 may. 2024", amount: 680, status: "Pendiente" },
  ],
  inventario: [
    { id: 1, title: "Bistec de Res", subtitle: "SKU: RES-001 · Res", stock: 45, price: 189, status: "Disponible" },
    { id: 2, title: "Costilla de Cerdo", subtitle: "SKU: CER-002 · Cerdo", stock: 30, price: 139, status: "Disponible" },
    { id: 3, title: "Pechuga de Pollo", subtitle: "SKU: POL-003 · Pollo", stock: 60, price: 129, status: "Disponible" },
    { id: 4, title: "Chuleta Ahumada", subtitle: "SKU: CER-004 · Cerdo", stock: 18, price: 169, status: "Disponible" },
  ],
  clientes: [
    { id: 1, title: "Juan Pérez", subtitle: "juan.perez@gmail.com · 55 1234 5678", amount: 12450, status: "Activo" },
    { id: 2, title: "María López", subtitle: "maria.lopez@gmail.com · 55 8765 4321", amount: 8230, status: "Activo" },
    { id: 3, title: "Cliente General", subtitle: "general@cliente.com", amount: 24780, status: "Activo" },
  ],
  proveedores: [
    { id: 1, title: "Carnes del Norte", subtitle: "contacto@carnesnorte.com · 55 2233 4455", status: "Activo" },
    { id: 2, title: "Distribuidora La Central", subtitle: "ventas@lacentral.com · 55 3344 5566", status: "Activo" },
    { id: 3, title: "Abastos Selectos", subtitle: "info@abastoselectos.com · 55 4455 6677", status: "Inactivo" },
  ],
  pedidos: [
    { id: 78, title: "#P-00078", subtitle: "Carnes del Norte · 16 may.", amount: 4230, status: "Pendiente" },
    { id: 77, title: "#P-00077", subtitle: "Distribuidora La Central · 14 may.", amount: 2980, status: "Recibido" },
  ],
  prestamos: [
    { id: 1, title: "Juan Pérez", subtitle: "Préstamo: $10,000 · Saldo: $6,250", status: "Activo" },
    { id: 2, title: "María López", subtitle: "Préstamo: $5,000 · Saldo: $3,234", status: "Activo" },
    { id: 3, title: "Luis Gómez", subtitle: "Préstamo: $8,000 · Saldo: $0", status: "Pagado" },
  ],
  nominas: [
    { id: 1, title: "Juan Martínez", subtitle: "Carnicero", amount: 2450 },
    { id: 2, title: "María Fernández", subtitle: "Caja", amount: 2250 },
    { id: 3, title: "Carlos Rodríguez", subtitle: "Almacén", amount: 2100 },
    { id: 4, title: "Ana Torres", subtitle: "Administración", amount: 2000 },
  ],
  rendimiento: [],
  informacion: [],
  empacadora: [
    { id: 1, title: "Venta empacadora #001", subtitle: "Lote A · Cliente Norte", amount: 12400, status: "Registrado" },
    { id: 2, title: "Lote de producción B", subtitle: "320 kg · En proceso", status: "Activo" },
  ],
  configuracion: [],
};

const emptyRecords = Object.fromEntries(
  (Object.keys(moduleInfo) as ModuleKey[]).map((module) => [module, [] as RecordItem[]]),
) as Record<ModuleKey, RecordItem[]>;

const money = (value = 0) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(value);

function parseSaleDate(value?: string) {
  if (!value) return null;
  const mexican = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$/);
  const date = mexican
    ? new Date(
        Number(mexican[3]),
        Number(mexican[2]) - 1,
        Number(mexican[1]),
        Number(mexican[4] ?? 0),
        Number(mexican[5] ?? 0),
        Number(mexican[6] ?? 0),
      )
    : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function buildChartPoints(records: RecordItem[], period: ChartPeriod): ChartPoint[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dayRange = period === "Hoy" ? 1 : period === "30 días" ? 30 : 7;
  const hours = [6, 9, 12, 15, 18, 21, 24];
  const points = Array.from({ length: 7 }, (_, index) => {
    if (period === "Hoy") {
      return { label: `${hours[index]}h`, detail: `${hours[index]}:00`, value: 0, operations: 0 };
    }
    const offset = Math.round((dayRange - 1) * (1 - index / 6));
    const date = new Date(today);
    date.setDate(today.getDate() - offset);
    return {
      label: period === "7 días"
        ? date.toLocaleDateString("es-MX", { weekday: "short" }).replace(".", "")
        : date.toLocaleDateString("es-MX", { day: "numeric", month: "short" }).replace(".", ""),
      detail: date.toLocaleDateString("es-MX", { weekday: "long", day: "numeric", month: "long" }),
      value: 0,
      operations: 0,
    };
  });

  records.forEach((record, index) => {
    const date = parseSaleDate(record.date);
    let bucket = Math.abs(record.id || index) % 7;
    if (date) {
      if (period === "Hoy") {
        if (date.toDateString() !== now.toDateString()) return;
        bucket = Math.max(0, Math.min(6, Math.floor((date.getHours() - 5) / 3)));
      } else {
        const saleDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        const age = Math.floor((today.getTime() - saleDay.getTime()) / 86_400_000);
        if (age < 0 || age >= dayRange) return;
        bucket = Math.max(0, Math.min(6, Math.round(((dayRange - 1 - age) / (dayRange - 1)) * 6)));
      }
    }
    points[bucket].value += record.amount ?? 0;
    points[bucket].operations += 1;
  });
  return points;
}

function apiPath(module: ModuleKey) {
  const paths: Partial<Record<ModuleKey, string>> = {
    ventas: "/api/ventas",
    compras: "/api/compras",
    inventario: "/api/articulos",
    clientes: "/api/clientes",
    proveedores: "/api/proveedores",
    pedidos: "/api/pedidos-proveedor",
    prestamos: "/api/mobile/modules/prestamos",
    nominas: "/api/mobile/modules/nominas",
    rendimiento: "/api/mobile/modules/rendimiento",
    informacion: "/api/mobile/modules/informacion",
    empacadora: "/api/mobile/modules/empacadora",
  };
  return paths[module];
}

const syncableModules = (Object.keys(moduleInfo) as ModuleKey[]).filter((module) => Boolean(apiPath(module)));

function apiPayload(module: ModuleKey, item: RecordItem) {
  const amount = item.amount ?? item.stock ?? 0;
  const title = item.title.trim();
  const subtitle = item.subtitle.trim();
  if (module === "inventario") return { codigo: subtitle || null, articulo: title, precio: item.price ?? 0, costo: 0, stock: Math.max(0, Math.round(amount)), estado: "activo" };
  if (module === "clientes") return { nombre: title, correo: subtitle || null };
  if (module === "proveedores") return { empresa: title, rif: subtitle || `APP-${Date.now()}` };
  if (module === "ventas") return { cliente: title || "Cliente General", items: [{ producto: subtitle, cantidad: Math.max(1, Math.round(amount || 1)) }] };
  if (module === "compras") return { proveedor: title, producto: subtitle || "Producto", cantidad: Math.max(1, Math.round(amount || 1)), costo_unitario: 0, estado: "Registrada" };
  if (module === "pedidos") return { proveedor_nombre: title, observaciones: subtitle || null, detalles: [] };
  if (module === "prestamos") return { beneficiario: title, concepto: subtitle, monto: amount };
  if (module === "nominas") return { empleado: title, puesto: "", periodo: subtitle || "Periodo actual", sueldo: amount, bonos: 0, deducciones: 0, notas: "" };
  if (module === "empacadora") return { cliente: title, folio: subtitle || `APP-${Date.now()}`, monto: amount, lote: "" };
  return { title, subtitle, amount };
}

function normalizeApiItems(module: ModuleKey, payload: unknown): RecordItem[] {
  const body = payload as { items?: Array<Record<string, unknown>> };
  const rows = Array.isArray(payload) ? (payload as Array<Record<string, unknown>>) : body?.items ?? [];
  if (module === "ventas") {
    return rows.map((row, index) => {
      const rawInvoice = row.factura ?? row.folio ?? row.id ?? row.row_id ?? index + 1;
      const invoice = String(rawInvoice).replace(/^#?V-?/i, "");
      const client = String(row.cliente ?? row.nombre_cliente ?? row.customer ?? "Cliente General");
      const product = String(row.articulo ?? row.producto ?? row.descripcion ?? row.codigo ?? "Venta registrada");
      const image = String(row.imagen_path ?? row.imagen ?? row.image ?? row.producto_imagen ?? row.foto ?? "");
      const time = String(row.hora ?? row.time ?? "");
      return {
        id: Number(row.id ?? row.row_id ?? index + 1),
        title: `#V-${invoice.padStart(5, "0")}`,
        subtitle: client,
        amount: Number(row.amount ?? row.total ?? row.monto ?? row.neto ?? 0) || undefined,
        status: String(row.status ?? row.estado ?? row.estatus ?? "Pagado"),
        price: row.precio == null ? undefined : Number(row.precio),
        date: row.fecha == null ? undefined : `${String(row.fecha)}${row.hora == null ? "" : ` ${String(row.hora)}`}`,
        image,
        client,
        product,
        time,
        invoice: rawInvoice as string | number,
      };
    });
  }
  return rows.map((row, index) => ({
    id: Number(row.id ?? row.row_id ?? index + 1),
    title: String(
      row.title ??
      row.articulo ??
      row.nombre ??
      row.cliente ??
      row.empresa ??
      row.proveedor_nombre ??
      row.proveedor ??
      row.empleado ??
      row.beneficiario ??
      row.producto ??
      row.folio ??
        `Registro ${index + 1}`,
    ),
    subtitle: String(
      row.subtitle ??
        row.producto ??
        row.codigo ??
        row.concepto ??
        row.periodo ??
        row.observaciones ??
        row.fecha ??
        row.correo ??
        row.rif ??
        "",
    ),
    amount: Number(row.amount ?? row.total ?? row.monto ?? row.neto ?? row.costo_total ?? 0) || undefined,
    status: String(row.status ?? row.estado ?? "Activo"),
    stock: row.stock == null ? undefined : Number(row.stock),
    price: row.precio == null ? undefined : Number(row.precio),
    date: row.fecha == null ? undefined : `${String(row.fecha)}${row.hora == null ? "" : ` ${String(row.hora)}`}`,
    image: String(row.imagen_path ?? row.imagen ?? row.image ?? row.foto ?? row.producto_imagen ?? ""),
  }));
}

function usesLocalApiProxy(serverUrl: string) {
  if (typeof window === "undefined") return false;
  try {
    const api = new URL(serverUrl);
    const app = new URL(window.location.href);
    return api.hostname === app.hostname && app.protocol === "http:" && api.protocol === "http:" && api.port !== app.port;
  } catch {
    return false;
  }
}

export default function Home() {
  const [splashVisible, setSplashVisible] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [sessionUser, setSessionUser] = useState("Usuario");
  const [sessionRole, setSessionRole] = useState("usuario");
  const [welcomeVisible, setWelcomeVisible] = useState(false);
  const [tab, setTab] = useState<Tab>("inicio");
  const [activeModule, setActiveModule] = useState<ModuleKey | null>(null);
  const [records, setRecords] = useState(emptyRecords);
  const [apiUrl, setApiUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [installPrompt, setInstallPrompt] = useState<Event | null>(null);
  const [toast, setToast] = useState("");
  const [modal, setModal] = useState<ModuleKey | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [jeloxFabVisible, setJeloxFabVisible] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<"demo" | "connecting" | "online" | "offline">("demo");
  const [lastSync, setLastSync] = useState<Date | null>(null);
  const [sessionNotice, setSessionNotice] = useState("");
  const [logoutConfirmVisible, setLogoutConfirmVisible] = useState(false);

  useEffect(() => {
    if (localStorage.getItem(ADMIN_ONLY_RESET_KEY) !== "done") {
      localStorage.removeItem(LEGACY_ACTIVE_SESSION_KEY);
      localStorage.removeItem(ACTIVE_SESSION_KEY);
      localStorage.removeItem("carnes-last-user");
      localStorage.removeItem("carnes-remembered-user");
      localStorage.removeItem("carnes-login-flow");
      localStorage.removeItem("carnes-trusted-device");
      Object.keys(localStorage)
        .filter((key) => key.startsWith("carnes-login-attempts:"))
        .forEach((key) => localStorage.removeItem(key));
      localStorage.setItem(ADMIN_ONLY_RESET_KEY, "done");
    }
    localStorage.removeItem("carnes-login-flow");
    if (readPendingMfaFlow()) setSplashVisible(false);
    setJeloxFabVisible(localStorage.getItem("jelox-fab-visible") !== "false");
    const hostname = window.location.hostname;
    const localNetworkHost =
      hostname === "localhost" ||
      hostname === "127.0.0.1" ||
      /^10\./.test(hostname) ||
      /^192\.168\./.test(hostname) ||
      /^172\.(1[6-9]|2\d|3[01])\./.test(hostname);
    const localServer = localNetworkHost
      ? `http://${hostname === "localhost" ? "127.0.0.1" : hostname}:8000`
      : "";
    const storedUrl = localStorage.getItem("carnes-api-url");
    const saved = localServer || storedUrl || "";
    if (localServer && storedUrl !== localServer) localStorage.setItem("carnes-api-url", localServer);
    const savedKey = localStorage.getItem("carnes-api-key") ?? "";
    setApiUrl(saved);
    setApiKey(savedKey);
    try {
      const stored = JSON.parse(localStorage.getItem(ACTIVE_SESSION_KEY) ?? "null") as { username?: string; role?: string; presentation?: boolean } | null;
      if (stored?.username && !stored.presentation) {
        setSessionUser(stored.username);
        setSessionRole(stored.role ?? "usuario");
        setAuthenticated(true);
      } else if (stored) {
        localStorage.removeItem(ACTIVE_SESSION_KEY);
      }
    } catch {
      localStorage.removeItem(ACTIVE_SESSION_KEY);
    }
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    const capture = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event);
    };
    window.addEventListener("beforeinstallprompt", capture);
    return () => window.removeEventListener("beforeinstallprompt", capture);
  }, []);

  function beginActiveSession(username: string, role = "usuario") {
    localStorage.setItem(ACTIVE_SESSION_KEY, JSON.stringify({ username, role, presentation: false }));
    setSessionNotice("");
    setSessionUser(username);
    setSessionRole(role);
    setAuthenticated(true);
    setWelcomeVisible(true);
  }

  function closeActiveSession() {
    localStorage.removeItem(ACTIVE_SESSION_KEY);
    setLogoutConfirmVisible(false);
    setAuthenticated(false);
    setSessionRole("usuario");
    setWelcomeVisible(false);
    setChatOpen(false);
    setTab("inicio");
    setActiveModule(null);
    setSessionNotice("");
  }

  function requestLogout() {
    setChatOpen(false);
    setLogoutConfirmVisible(true);
  }

  useEffect(() => {
    if (!logoutConfirmVisible) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setLogoutConfirmVisible(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [logoutConfirmVisible]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(""), 2600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function callApi(
    path: string,
    options?: RequestInit,
    connection?: ApiConnection,
  ) {
    const serverUrl = connection?.url ?? apiUrl;
    const serverKey = connection?.key ?? apiKey;
    if (!serverUrl) throw new Error("Servidor no configurado");
    const normalizedServerUrl = serverUrl.replace(/\/$/, "");
    const useProxy = usesLocalApiProxy(normalizedServerUrl);
    const response = await fetch(useProxy ? `${LOCAL_API_PROXY_PREFIX}${path}` : `${normalizedServerUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(useProxy ? { "x-carnes-api-url": normalizedServerUrl } : {}),
        ...(serverKey ? { "x-api-key": serverKey } : {}),
        ...(options?.headers ?? {}),
      },
    });
    if (!response.ok) {
      const error = (await response.json().catch(() => ({ detail: "Error de servidor" }))) as {
        detail?: string | AuthDetail;
      };
      throw new ApiResponseError(response.status, error.detail ?? "No se pudo completar");
    }
    return response.status === 204 ? null : response.json();
  }

  useEffect(() => {
    if (!authenticated || !apiUrl || ["super", "administrador", "admin"].includes(sessionRole.toLowerCase())) return;
    let active = true;
    callApi(`/api/mobile/admin?actor=${encodeURIComponent(sessionUser)}`)
      .then(() => {
        if (!active) return;
        setSessionRole("administrador");
        try {
          const stored = JSON.parse(localStorage.getItem(ACTIVE_SESSION_KEY) ?? "null") as Record<string, unknown> | null;
          if (stored) localStorage.setItem(ACTIVE_SESSION_KEY, JSON.stringify({ ...stored, role: "administrador" }));
        } catch {
          // La sesión actual sigue siendo válida aunque no pueda actualizarse la copia local.
        }
      })
      .catch(() => undefined);
    return () => { active = false; };
  }, [authenticated, apiUrl, sessionRole, sessionUser]);

  useEffect(() => {
    if (!authenticated || !apiUrl) {
      setConnectionStatus("demo");
      return;
    }

    let active = true;
    const selectedModules: ModuleKey[] = activeModule && apiPath(activeModule) ? [activeModule] : syncableModules;

    async function synchronize() {
      setConnectionStatus((current) => (current === "online" ? current : "connecting"));
      try {
        await callApi("/api/health");
        const responses = await Promise.allSettled(
          selectedModules.map(async (module) => ({
            module,
            payload: await callApi(apiPath(module)!),
          })),
        );
        if (!active) return;
        setRecords((current) => {
          const updated = { ...current };
          for (const response of responses) {
            if (response.status !== "fulfilled") continue;
            const items = normalizeApiItems(response.value.module, response.value.payload);
            updated[response.value.module] = items;
          }
          return updated;
        });
        setConnectionStatus("online");
        setLastSync(new Date());
      } catch {
        if (active) setConnectionStatus("offline");
      }
    }

    synchronize();
    const timer = window.setInterval(synchronize, 2000);
    const onVisible = () => {
      if (document.visibilityState === "visible") synchronize();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      active = false;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [authenticated, apiUrl, apiKey, activeModule, tab]);

  async function openModule(module: ModuleKey) {
    setActiveModule(module);
    const path = apiPath(module);
    if (!path || !apiUrl) return;
    try {
      const payload = await callApi(path);
      const items = normalizeApiItems(module, payload);
      setRecords((current) => ({ ...current, [module]: items }));
    } catch {
      setToast("Mostrando datos guardados; revisa la conexión API");
    }
  }

  async function saveRecord(module: ModuleKey, item: RecordItem) {
    const path = apiPath(module);
    if (!path || !apiUrl) throw new Error("Este módulo necesita conexión con la API para guardar.");
    await callApi(path, { method: "POST", body: JSON.stringify(apiPayload(module, item)) });
    const payload = await callApi(path);
    const syncedItems = normalizeApiItems(module, payload);
    setRecords((current) => ({ ...current, [module]: syncedItems }));
    setLastSync(new Date());
  }

  async function deleteRecord(module: ModuleKey, id: number) {
    const path = apiPath(module);
    const supportsDelete = ["inventario", "clientes", "proveedores"].includes(module);
    if (path && apiUrl && supportsDelete) {
      await callApi(`${path}/${id}`, { method: "DELETE" });
    }
    setRecords((current) => ({ ...current, [module]: current[module].filter((item) => item.id !== id) }));
  }

  async function refreshDashboard() {
    const modules = syncableModules;
    setConnectionStatus("connecting");
    try {
      await callApi("/api/health");
      const responses = await Promise.all(
        modules.map(async (module) => ({
          module,
          payload: await callApi(apiPath(module)!),
        })),
      );
      setRecords((current) => {
        const updated = { ...current };
        responses.forEach(({ module, payload }) => {
          const items = normalizeApiItems(module, payload);
          updated[module] = items;
        });
        return updated;
      });
      setLastSync(new Date());
      setConnectionStatus("online");
      setToast("Información actualizada desde el sistema");
    } catch {
      setConnectionStatus("offline");
      setToast("No se pudo sincronizar. Revisa que el sistema de la PC esté abierto.");
    }
  }

  async function install() {
    if (installPrompt && "prompt" in installPrompt) {
      await (installPrompt as Event & { prompt: () => Promise<void> }).prompt();
    } else {
      setToast("En Safari toca Compartir y luego “Agregar a inicio”");
    }
  }

  function saveApi(url: string, key: string) {
    localStorage.setItem("carnes-api-url", url);
    localStorage.setItem("carnes-api-key", key);
    setApiUrl(url);
    setApiKey(key);
  }

  if (splashVisible) {
    return <SplashScreen onComplete={() => setSplashVisible(false)} />;
  }

  if (!authenticated) {
    return (
      <Login
        apiUrl={apiUrl}
        apiKey={apiKey}
        sessionNotice={sessionNotice}
        saveApi={saveApi}
        callApi={callApi}
        onLogin={beginActiveSession}
      />
    );
  }

  return (
    <main className="app">
      {activeModule ? (
        <ModuleView
          module={activeModule}
          records={records[activeModule]}
          allRecords={records}
          onBack={() => setActiveModule(null)}
          onAdd={() => setModal(activeModule)}
          onDelete={(id) => deleteRecord(activeModule, id).catch((error) => setToast(error instanceof Error ? error.message : "No se pudo eliminar"))}
          connectionStatus={connectionStatus}
          username={sessionUser}
          onModule={openModule}
          onQuickAdd={(module) => setModal(module)}
          onLogout={requestLogout}
        />
      ) : tab === "inicio" ? (
        <Dashboard
          records={records}
          onModule={openModule}
          onQuickAdd={(module) => setModal(module)}
          onRefresh={refreshDashboard}
          connectionStatus={connectionStatus}
          lastSync={lastSync}
          username={sessionUser}
          showWelcome={welcomeVisible}
          onDismissWelcome={() => setWelcomeVisible(false)}
          onLogout={requestLogout}
        />
      ) : tab === "reportes" ? (
        <ReportsCenter
          records={records}
          username={sessionUser}
          connectionStatus={connectionStatus}
          onModule={openModule}
          onQuickAdd={(module) => setModal(module)}
          onLogout={requestLogout}
        />
      ) : tab === "jelox" ? (
        <JeloxAiCenter
          username={sessionUser}
          records={records}
          connectionStatus={connectionStatus}
          onQuickAdd={(module) => setModal(module)}
          callApi={callApi}
        />
      ) : tab === "bandeja" ? (
        <NotificationInbox records={records} connectionStatus={connectionStatus} onModule={openModule} />
      ) : tab === "usuarios" ? (
        <ModuleHub
          onModule={openModule}
          username={sessionUser}
          connectionStatus={connectionStatus}
          callApi={callApi}
          usersOnly
        />
      ) : (
        <ModuleHub
          onModule={openModule}
          username={sessionUser}
          connectionStatus={connectionStatus}
          callApi={callApi}
        />
      )}

      <BottomNav
        tab={activeModule ? "administrar" : tab}
        isAdmin={["super", "administrador", "admin"].includes(sessionRole.toLowerCase())}
        onChange={(next) => { setTab(next); setActiveModule(null); }}
      />
      {tab !== "jelox" && jeloxFabVisible && <MovableJeloxButton onOpen={() => setChatOpen(true)} />}
      {chatOpen && (
        <JeloxChat
          callApi={callApi}
          username={sessionUser}
          onClose={() => setChatOpen(false)}
          fabVisible={jeloxFabVisible}
          onFabVisibilityChange={(visible) => {
            setJeloxFabVisible(visible);
            localStorage.setItem("jelox-fab-visible", String(visible));
          }}
        />
      )}
      {modal && (
        <RecordModal
          module={modal}
          onClose={() => setModal(null)}
          onSave={async (item) => {
            const selectedModule = modal;
            await saveRecord(selectedModule, item);
            setModal(null);
            setToast("Registro guardado y sincronizado con el sistema");
          }}
        />
      )}
      {logoutConfirmVisible && (
        <div
          className="logout-confirm-backdrop"
          onPointerDown={(event) => {
            if (event.target === event.currentTarget) setLogoutConfirmVisible(false);
          }}
        >
          <section
            className="logout-confirm-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="logout-confirm-title"
            aria-describedby="logout-confirm-description"
          >
            <span className="logout-confirm-icon"><img src="/icons/log-out.svg" alt="" /></span>
            <small>Sesión protegida</small>
            <h2 id="logout-confirm-title">¿Cerrar sesión?</h2>
            <p id="logout-confirm-description">
              Se cerrará la sesión de <strong>{sessionUser}</strong> en este dispositivo.
              Tendrás que volver a identificarte para entrar.
            </p>
            <div className="logout-confirm-user">
              <span>{sessionUser.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase()}</span>
              <div><strong>{sessionUser}</strong><small>Conexión segura con JELOX</small></div>
              <i />
            </div>
            <div className="logout-confirm-actions">
              <button type="button" onClick={() => setLogoutConfirmVisible(false)}>Cancelar</button>
              <button type="button" className="danger" onClick={closeActiveSession}>
                <img src="/icons/log-out.svg" alt="" />Cerrar sesión
              </button>
            </div>
          </section>
        </div>
      )}
      {toast && <div className="toast">{toast}</div>}
    </main>
  );
}

function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(6);
  const [status, setStatus] = useState("Preparando acceso local…");
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let completed = false;
    const startedAt = Date.now();
    const smoothProgress = window.setInterval(() => {
      setProgress((current) => (current < 94 ? current + 4 : current));
    }, 45);
    const finishSplash = () => {
      if (cancelled || completed) return;
      completed = true;
      window.clearInterval(smoothProgress);
      setStatus("Acceso listo");
      setProgress(100);
      setLeaving(true);
      window.setTimeout(() => {
        if (!cancelled) onComplete();
      }, 180);
    };
    const hardStop = window.setTimeout(finishSplash, 1200);

    const preload = (src: string) =>
      new Promise<void>((resolve) => {
        const image = new Image();
        const timeout = window.setTimeout(resolve, 450);
        image.onload = () => {
          window.clearTimeout(timeout);
          resolve();
        };
        image.onerror = () => {
          window.clearTimeout(timeout);
          resolve();
        };
        image.src = src;
      });

    async function prepare() {
      await Promise.race([
        Promise.all([preload("/logo-luevanos.png"), preload("/splash-bg.png"), preload("/jelox.png")]),
        new Promise((resolve) => window.setTimeout(resolve, 500)),
      ]);
      if (cancelled) return;
      setProgress((current) => Math.max(current, 38));
      setStatus("Cargando recursos locales…");

      await Promise.race([
        document.fonts?.ready ?? Promise.resolve(),
        new Promise((resolve) => window.setTimeout(resolve, 250)),
      ]);
      if (cancelled) return;
      setProgress((current) => Math.max(current, 58));
      setStatus("Buscando el sistema…");

      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 1800);
      try {
        const localApi = `http://${window.location.hostname}:8000/api/health`;
        const response = await fetch(localApi, { signal: controller.signal, cache: "no-store" });
        setStatus(response.ok ? "Conexión con el sistema lista" : "Preparando acceso local…");
      } catch {
        setStatus("Preparando acceso local…");
      } finally {
        window.clearTimeout(timeout);
      }

      if (cancelled) return;
      setProgress((current) => Math.max(current, 84));
      const remaining = Math.max(0, 900 - (Date.now() - startedAt));
      await new Promise((resolve) => window.setTimeout(resolve, remaining));
      if (cancelled) return;

      finishSplash();
    }

    prepare().catch(finishSplash);
    return () => {
      cancelled = true;
      window.clearTimeout(hardStop);
      window.clearInterval(smoothProgress);
    };
  }, [onComplete]);

  return (
    <main className={`splash-screen${leaving ? " leaving" : ""}`} aria-label="Cargando Carnes Luévanos">
      <div className="splash-vignette" />
      <section className="splash-brand">
        <div className="splash-logo">
          <img src="/logo-luevanos.png" alt="Carnes Luévanos" />
        </div>
        <h1>CARNES<br />LUÉVANOS</h1>
        <p>Sistema Administrativo</p>
      </section>
      <section className="splash-loader" aria-live="polite">
        <div className="splash-loading-copy">
          <span>{status}</span>
          <strong>{progress}%</strong>
        </div>
        <div
          className="splash-progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
        >
          <span style={{ width: `${progress}%` }} />
        </div>
      </section>
    </main>
  );
}

function Login({
  apiUrl,
  apiKey,
  sessionNotice,
  saveApi,
  callApi,
  onLogin,
}: {
  apiUrl: string;
  apiKey: string;
  sessionNotice: string;
  saveApi: (url: string, key: string) => void;
  callApi: (path: string, options?: RequestInit, connection?: ApiConnection) => Promise<unknown>;
  onLogin: (username: string, role?: string) => void;
}) {
  const pendingMfaFlow = useRef<PendingMfaFlow | null>(readPendingMfaFlow()).current;
  const [step, setStep] = useState<LoginStep>(pendingMfaFlow?.step ?? "credentials");
  const [user, setUser] = useState(pendingMfaFlow?.user ?? "");
  const [password, setPassword] = useState(pendingMfaFlow?.password ?? "");
  const [otp, setOtp] = useState("");
  const [server, setServer] = useState(apiUrl);
  const [key, setKey] = useState(apiKey);
  const [deviceToken, setDeviceToken] = useState("");
  const [showServer, setShowServer] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [online, setOnline] = useState<boolean | null>(null);
  const [securityView, setSecurityView] = useState<"forgot" | "touch" | "locked" | "unlock" | null>(null);
  const [remainingAttempts, setRemainingAttempts] = useState<number | null>(null);
  const [lockedUser, setLockedUser] = useState("");
  const [adminUser, setAdminUser] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [securityMessage, setSecurityMessage] = useState("");
  const [otpHelp, setOtpHelp] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [mfaSetup, setMfaSetup] = useState<{ secret: string; userId: number } | null>(pendingMfaFlow?.mfaSetup ?? null);
  const loginSound = useRef<AudioContext | null>(null);

  useEffect(() => {
    localStorage.removeItem("carnes-login-flow");
    const lastUser =
      localStorage.getItem("carnes-last-user") ||
      localStorage.getItem("carnes-remembered-user");
    if (lastUser) {
      setUser(lastUser);
      setRemember(true);
    }
    let trustedDevice = localStorage.getItem("carnes-trusted-device");
    if (!trustedDevice) {
      trustedDevice =
        typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
      localStorage.setItem("carnes-trusted-device", trustedDevice);
    }
    setDeviceToken(trustedDevice);
  }, []);

  useEffect(() => {
    if (step === "credentials" || !user || !password) return;
    const flow: PendingMfaFlow = {
      step,
      user,
      password,
      mfaSetup,
      savedAt: Date.now(),
    };
    sessionStorage.setItem(PENDING_MFA_FLOW_KEY, JSON.stringify(flow));
  }, [step, user, password, mfaSetup]);

  useEffect(() => {
    if (!apiUrl) return;
    setServer(apiUrl);
    setShowServer(false);
  }, [apiUrl]);

  const connection = { url: server, key };

  useEffect(() => {
    if (!server) {
      setOnline(false);
      return;
    }
    let active = true;
    fetch(`${server.replace(/\/$/, "")}/api/health`, { headers: key ? { "X-API-Key": key } : {} })
      .then((response) => {
        if (active) setOnline(response.ok);
      })
      .catch(() => {
        if (active) setOnline(false);
      });
    return () => {
      active = false;
    };
  }, [server, key]);

  async function loginWithOtp(code?: string) {
    return callApi(
      "/api/auth/login",
      {
        method: "POST",
        body: JSON.stringify({
          username: user,
          password,
          otp: code || undefined,
          device_token: deviceToken || undefined,
        }),
      },
      connection,
    );
  }

  async function notifyIphoneLogin(username: string) {
    if (!window.isSecureContext || !("Notification" in window)) return;
    try {
      const permission =
        Notification.permission === "default"
          ? await Notification.requestPermission()
          : Notification.permission;
      if (permission !== "granted") return;
      const registration = "serviceWorker" in navigator ? await navigator.serviceWorker.ready : null;
      const options = {
        body: `${username} ingresó correctamente al sistema.`,
        icon: "/jelox-welcome-hd.png",
        badge: "/jelox-welcome-hd.png",
        tag: `jelox-login-${username}`,
      };
      if (registration) await registration.showNotification("JELOX · Inicio de sesión", options);
      else new Notification("JELOX · Inicio de sesión", options);
    } catch {
      // La bienvenida dentro de la app sigue confirmando el acceso.
    }
  }

  function prepareJeloxSound() {
    try {
      if (!loginSound.current) loginSound.current = new AudioContext();
      void loginSound.current.resume();
    } catch {
      loginSound.current = null;
    }
  }

  function playJeloxSound() {
    const context = loginSound.current;
    if (!context) return;
    const start = context.currentTime + 0.02;
    const notes = [
      { frequency: 523.25, offset: 0, duration: 0.16, volume: 0.055 },
      { frequency: 659.25, offset: 0.13, duration: 0.2, volume: 0.05 },
      { frequency: 987.77, offset: 0.29, duration: 0.32, volume: 0.045 },
    ];
    notes.forEach((note) => {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(note.frequency, start + note.offset);
      gain.gain.setValueAtTime(0.0001, start + note.offset);
      gain.gain.exponentialRampToValueAtTime(note.volume, start + note.offset + 0.025);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + note.offset + note.duration);
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start(start + note.offset);
      oscillator.stop(start + note.offset + note.duration + 0.03);
    });
    window.setTimeout(() => {
      void context.close();
      if (loginSound.current === context) loginSound.current = null;
    }, 900);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    prepareJeloxSound();
    setBusy(true);
    setError("");
    saveApi(server, key);
    if (!server) {
      setBusy(false);
      setError("Abre el sistema administrativo para activar la conexión.");
      return;
    }
    try {
      let loginResult: { username?: string; role?: string } | null = null;
      if (step === "setup" && mfaSetup) {
        await callApi(
          "/api/auth/mfa/enable",
          {
            method: "POST",
            body: JSON.stringify({ user_id: mfaSetup.userId, secret: mfaSetup.secret, code: otp }),
          },
          connection,
        );
        loginResult = (await loginWithOtp(otp)) as { username?: string; role?: string };
      } else {
        loginResult = (await loginWithOtp(step === "mfa" ? otp : undefined)) as { username?: string; role?: string };
      }
      if (remember) localStorage.setItem("carnes-remembered-user", user.trim());
      else localStorage.removeItem("carnes-remembered-user");
      localStorage.removeItem(`carnes-login-attempts:${user.trim().toLowerCase()}`);
      const verifiedUser = loginResult?.username || user.trim();
      localStorage.setItem("carnes-last-user", verifiedUser);
      sessionStorage.removeItem(PENDING_MFA_FLOW_KEY);
      setPassword("");
      setOtp("");
      await notifyIphoneLogin(verifiedUser);
      playJeloxSound();
      onLogin(verifiedUser, loginResult?.role ?? "usuario");
    } catch (err) {
      if (err instanceof ApiResponseError && err.status === 428 && typeof err.detail !== "string") {
        const detail = err.detail;
        if (detail.mfa_setup_required && detail.secret && detail.user_id) {
          setMfaSetup({ secret: detail.secret, userId: detail.user_id });
          setStep("setup");
          setOtp("");
          setError("");
          return;
        }
        setStep("mfa");
        setOtp("");
        setError(detail.message ?? "Ingresa el código de autenticación.");
        return;
      }
      if (err instanceof ApiResponseError && err.status === 401) {
        const detail = typeof err.detail === "string" ? { message: err.detail } : err.detail;
        const attemptKey = `carnes-login-attempts:${user.trim().toLowerCase()}`;
        const fallbackAttempts = Math.min(5, Number(localStorage.getItem(attemptKey) || "0") + 1);
        const attempts = detail.failed_attempts ?? fallbackAttempts;
        const remaining = detail.remaining_attempts ?? Math.max(0, 5 - attempts);
        localStorage.setItem(attemptKey, String(attempts));
        setRemainingAttempts(remaining);
        if (detail.admin_unlock_required || remaining === 0) {
          setLockedUser(detail.locked_username || user.trim());
          setSecurityView("locked");
          setError("");
          return;
        }
        setError(detail.message || `Credenciales incorrectas. Quedan ${remaining} intentos.`);
        return;
      }
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión");
    } finally {
      setBusy(false);
    }
  }

  const otpUri =
    mfaSetup &&
    `otpauth://totp/Carnes%20Lu%C3%A9vanos:${encodeURIComponent(user)}?secret=${mfaSetup.secret}&issuer=Carnes%20Lu%C3%A9vanos`;

  function openTouchId() {
    if (!window.isSecureContext) {
      setSecurityMessage("Touch ID requiere una conexión HTTPS segura. En la dirección local HTTP puedes iniciar sesión con usuario, contraseña y verificación en dos pasos.");
    } else if (!("PublicKeyCredential" in window)) {
      setSecurityMessage("Este navegador no permite Touch ID para esta aplicación. Usa tu contraseña para continuar.");
    } else {
      setSecurityMessage("Touch ID está disponible en este iPhone, pero primero debe registrarse desde una sesión segura del sistema.");
    }
    setSecurityView("touch");
  }

  async function unlockAccount(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setSecurityMessage("");
    try {
      const result = (await callApi(
        "/api/auth/unlock",
        {
          method: "POST",
          body: JSON.stringify({
            locked_username: lockedUser,
            admin_username: adminUser,
            admin_password: adminPassword,
          }),
        },
        connection,
      )) as { message?: string };
      localStorage.removeItem(`carnes-login-attempts:${lockedUser.toLowerCase()}`);
      setRemainingAttempts(null);
      setAdminUser("");
      setAdminPassword("");
      setPassword("");
      setSecurityMessage(result.message || "La cuenta fue desbloqueada correctamente.");
      setSecurityView("unlock");
    } catch (err) {
      setSecurityMessage(err instanceof Error ? err.message : "No se pudo desbloquear la cuenta.");
    } finally {
      setBusy(false);
    }
  }

  function closeSecurityView() {
    setSecurityView(null);
    setSecurityMessage("");
    setAdminPassword("");
  }

  return (
    <main className={`login-screen ${step === "credentials" ? "" : "verification-screen"}`}>
      <section className={`login-card ${step === "credentials" ? "" : "verification-card"}`}>
        <div className={step === "credentials" ? "login-logo" : "google-auth-logo"}>
          <img
            src={step === "credentials" ? "/logo-luevanos.png" : "/google-authenticator.png"}
            alt={step === "credentials" ? "Carnes Luévanos" : "Google Authenticator"}
          />
        </div>
        <h1>{step === "credentials" ? (user.trim() ? `Bienvenido, ${user.trim()}` : "Bienvenido") : "Verificación en dos pasos"}</h1>
        <p className="muted">
          {step === "credentials"
            ? "Inicia sesión para continuar"
            : step === "setup"
              ? "Configura un autenticador antes de continuar"
              : "Ingresa el código de 6 dígitos de tu autenticador"}
        </p>
        {sessionNotice && <div className="session-expired-notice"><span>i</span><p>{sessionNotice}</p></div>}

        {securityView ? (
          <div className={`security-card-view ${securityView === "locked" ? "danger" : ""}`}>
            <div className="security-card-icon">
              {securityView === "locked" ? "!" : securityView === "unlock" ? "✓" : securityView === "touch" ? "◎" : "?"}
            </div>
            <h2>
              {securityView === "locked"
                ? "Cuenta bloqueada"
                : securityView === "unlock"
                  ? "Cuenta desbloqueada"
                  : securityView === "touch"
                    ? "Touch ID"
                    : "Recuperar acceso"}
            </h2>
            {securityView === "locked" ? (
              <>
                <p>Se alcanzaron los 5 intentos permitidos para <strong>{lockedUser}</strong>.</p>
                <p className="security-note">Por seguridad, solo un administrador puede desbloquear esta cuenta con su contraseña.</p>
                <form onSubmit={unlockAccount} className="unlock-form">
                  <div className="login-field">
                    <span className="field-icon">♙</span>
                    <input value={adminUser} onChange={(e) => setAdminUser(e.target.value)} placeholder="Usuario administrador" autoComplete="username" required />
                  </div>
                  <div className="login-field">
                    <span className="field-icon">◇</span>
                    <input value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} placeholder="Contraseña del administrador" type="password" autoComplete="current-password" required />
                  </div>
                  {securityMessage && <p className="error">{securityMessage}</p>}
                  <button className="primary" disabled={busy}>{busy ? "Verificando…" : "Desbloquear cuenta"}</button>
                </form>
              </>
            ) : (
              <>
                <p>
                  {securityView === "forgot"
                    ? "Solicita a un administrador que restablezca tus credenciales desde el sistema de escritorio."
                    : securityMessage}
                </p>
                {securityView === "forgot" && <p className="security-note">Nunca se envían ni se muestran contraseñas desde esta app.</p>}
                <button className="primary" type="button" onClick={closeSecurityView}>Volver al inicio</button>
              </>
            )}
          </div>
        ) : (
        <form
          key={step}
          onSubmit={submit}
          className="login-form"
          autoComplete="off"
        >
          {step === "credentials" ? (
            <>
              <div className="login-field">
                <span className="field-icon user-icon" aria-hidden="true" />
                <input name="username" value={user} onChange={(e) => setUser(e.target.value)} autoComplete="username" autoCapitalize="none" spellCheck={false} placeholder="Usuario" aria-label="Usuario" required />
              </div>
              <div className="login-field">
                <span className="field-icon lock-icon" aria-hidden="true" />
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  name="carnes-access-secret"
                  type="text"
                  className={`secure-password-input ${showPassword ? "visible" : "masked"}`}
                  autoComplete="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  data-form-type="other"
                  data-1p-ignore="true"
                  placeholder="Contraseña"
                  aria-label="Contraseña"
                  required
                />
                <button type="button" className={`password-toggle eye-icon ${showPassword ? "open" : "closed"}`} onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"} />
              </div>
              <div className="login-options">
                <label className="remember-control">
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                  <span>Recordarme</span>
                </label>
                <button type="button" onClick={() => setSecurityView("forgot")}>¿Olvidaste tu contraseña?</button>
              </div>
              {remainingAttempts !== null && remainingAttempts > 0 && (
                <div className="attempt-card">
                  <strong>Acceso no verificado</strong>
                  <span>Te quedan {remainingAttempts} de 5 intentos antes del bloqueo.</span>
                </div>
              )}
              {showServer && (
                <div className="server-fields">
                  <label>
                    Dirección de la API
                    <input
                      value={server}
                      onChange={(e) => setServer(e.target.value)}
                      placeholder="http://192.168.1.8:8000"
                      inputMode="url"
                    />
                  </label>
                  <label>
                    Clave de API
                    <input value={key} onChange={(e) => setKey(e.target.value)} type="password" />
                  </label>
                </div>
              )}
            </>
          ) : (
            <>
              {step === "setup" && mfaSetup && (
                <div className="mfa-setup">
                  <strong>Configura Google Authenticator</strong>
                  <ol>
                    <li>Abre Google Authenticator en tu iPhone.</li>
                    <li>Selecciona «Agregar una clave de configuración».</li>
                    <li>Copia la clave mostrada abajo e ingresa el código generado.</li>
                  </ol>
                  <button
                    type="button"
                    className="secret-key"
                    onClick={() => navigator.clipboard?.writeText(mfaSetup.secret)}
                  >
                    <span>Clave de configuración</span>
                    <code>{mfaSetup.secret}</code>
                    <small>Toca para copiar</small>
                  </button>
                  {otpUri && <a className="auth-link" href={otpUri}>Abrir en un autenticador compatible</a>}
                </div>
              )}
              <label className="otp-control">
                <span className="sr-only">Código de verificación</span>
                <input
                  className="otp-hidden"
                  value={otp}
                  onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  name="one-time-code"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  placeholder="000000"
                  pattern="\d{6}"
                  maxLength={6}
                  required
                  autoFocus
                />
                <span className="otp-boxes" aria-hidden="true">
                  {Array.from({ length: 6 }, (_, index) => (
                    <span className={`otp-digit google-${index % 4}`} key={index}>
                      {otp[index] || ""}
                    </span>
                  ))}
                </span>
              </label>
              <div className="google-color-line" aria-hidden="true">
                <span /><span /><span /><span />
              </div>
              <button type="button" className="otp-help-button" onClick={() => setOtpHelp(!otpHelp)}>
                {otpHelp ? "Ocultar ayuda" : "¿Dónde encuentro el código?"}
              </button>
              {otpHelp && (
                <div className="otp-help-card">
                  Abre Google Authenticator y usa el código de 6 dígitos asociado a Carnes Luévanos. El código cambia cada 30 segundos.
                </div>
              )}
            </>
          )}
          {error && <p className="error">{error}</p>}
          <button className="primary" disabled={busy || !server || (step !== "credentials" && otp.length !== 6)}>
            {busy
              ? "Verificando…"
              : step === "setup"
                ? "Activar y verificar"
                  : step === "mfa"
                  ? "Verificar código"
                  : server
                    ? "Iniciar sesión"
                    : "Detectando sistema…"}
          </button>
        </form>
        )}
        {!securityView && step === "credentials" ? (
          <>
            <div className="login-divider"><span>Acceso protegido</span></div>
            <div className="connection-line">
              <span className={online ? "online" : "offline"} />
              {online ? "Sistema conectado" : "Sistema sin conexión"}
              <button type="button" onClick={() => setShowServer(!showServer)}>{showServer ? "Ocultar" : "Configurar"}</button>
            </div>
          </>
        ) : !securityView ? (
          <button
            className="text-button back-login"
            onClick={() => {
              sessionStorage.removeItem(PENDING_MFA_FLOW_KEY);
              setStep("credentials");
              setOtp("");
              setPassword("");
              setError("");
              setMfaSetup(null);
            }}
          >
            Volver al inicio de sesión
          </button>
        ) : null}
        <footer className="login-footer">
          <span>© 2026 Carnes Luévanos</span>
          <span>Todos los derechos reservados</span>
        </footer>
      </section>
    </main>
  );
}

function SecureWelcomeLoader({
  username,
  onComplete,
}: {
  username: string;
  onComplete: () => void;
}) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const startedAt = performance.now();
    const timer = window.setInterval(() => {
      const elapsed = performance.now() - startedAt;
      setProgress(Math.min(100, Math.floor((elapsed / 3000) * 100)));
    }, 50);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (progress < 100) return;
    const finish = window.setTimeout(onComplete, 600);
    return () => window.clearTimeout(finish);
  }, [progress, onComplete]);

  return (
    <div className="secure-loader-overlay">
      <article className={`secure-loader-card ${progress === 100 ? "is-complete" : ""}`} role="dialog" aria-modal="true" aria-label={`Bienvenido, ${username}. Preparando panel seguro`}>
        <div className="secure-loader-logo">
          <span><img src="/jelox-welcome-hd.png" alt="JELOX Studio" /></span>
        </div>
        <div className="welcome-progress-eyebrow"><span /> Acceso verificado</div>
        <h2>¡Bienvenido, <span>{username}</span>!</h2>
        <p>{progress === 100 ? "Tu panel está listo" : "Estamos preparando tu espacio de trabajo protegido por JELOX Studio"}</p>
        <div className="secure-progress" aria-label={`Carga ${progress}%`}>
          <span style={{ width: `${progress}%` }} />
        </div>
        <div className="secure-progress-copy">
          <span>{progress === 100 ? "Protección activada" : "Cargando entorno seguro…"}</span>
          <strong>{progress}%</strong>
        </div>
        <div className="end-to-end-card">
          <span className="security-lock" aria-hidden="true" />
          <p><strong>Protección de extremo a extremo</strong>Toda tu información está cifrada. Solo tus dispositivos autorizados pueden acceder a ella.</p>
        </div>
      </article>
    </div>
  );
}

const sidebarItems: Array<{ label: string; icon: string; module?: ModuleKey }> = [
  { label: "Inicio", icon: "house" },
  { label: "Ventas", icon: "receipt-text", module: "ventas" },
  { label: "Compras", icon: "shopping-cart", module: "compras" },
  { label: "Inventario", icon: "package", module: "inventario" },
  { label: "Clientes", icon: "users", module: "clientes" },
  { label: "Proveedores", icon: "truck", module: "proveedores" },
  { label: "Pedidos", icon: "clipboard-list", module: "pedidos" },
  { label: "Préstamos y abonos", icon: "hand-coins", module: "prestamos" },
  { label: "Nóminas", icon: "wallet-cards", module: "nominas" },
  { label: "Rendimiento", icon: "chart-line", module: "rendimiento" },
  { label: "Información", icon: "info", module: "informacion" },
  { label: "Configuración", icon: "settings", module: "configuracion" },
];

const creationActions: Array<{ module: ModuleKey; label: string; detail: string; icon: string }> = [
  { module: "ventas", label: "Nueva venta", detail: "Registrar una operación", icon: "receipt-text" },
  { module: "compras", label: "Nueva compra", detail: "Registrar una compra", icon: "shopping-cart" },
  { module: "inventario", label: "Nuevo producto", detail: "Agregar al inventario", icon: "package" },
  { module: "clientes", label: "Nuevo cliente", detail: "Crear un contacto", icon: "user-plus" },
  { module: "proveedores", label: "Nuevo proveedor", detail: "Registrar proveedor", icon: "truck" },
  { module: "pedidos", label: "Nuevo pedido", detail: "Pedido a proveedor", icon: "clipboard-list" },
  { module: "prestamos", label: "Préstamo o abono", detail: "Registrar movimiento", icon: "hand-coins" },
  { module: "nominas", label: "Registro de nómina", detail: "Agregar pago de nómina", icon: "wallet-cards" },
  { module: "empacadora", label: "Registro de empacadora", detail: "Agregar operación o lote", icon: "package" },
];

function SidebarMenu({
  username,
  onClose,
  onModule,
  onLogout,
}: {
  username: string;
  onClose: () => void;
  onModule: (module: ModuleKey) => void;
  onLogout: () => void;
}) {
  return (
    <div className="sidebar-backdrop" role="presentation" onClick={onClose}>
      <aside className="user-sidebar" aria-label="Menú principal" onClick={(event) => event.stopPropagation()}>
        <header>
          <img className="sidebar-brand-logo" src="/logo-luevanos.png" alt="Carnes Luévanos" />
          <div>
            <strong>{username}</strong>
            <span>Usuario verificado</span>
          </div>
          <button type="button" onClick={onClose} aria-label="Cerrar menú"><img src="/icons/x.svg" alt="" /></button>
        </header>
        <nav>
          {sidebarItems.map((item) => (
            <button
              className={!item.module ? "active" : ""}
              key={item.label}
              type="button"
              onClick={() => item.module ? onModule(item.module) : onClose()}
            >
              <img src={`/icons/${item.icon}.svg`} alt="" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <button className="sidebar-logout" type="button" onClick={onLogout}>
          <img src="/icons/log-out.svg" alt="" />
          <span>Cerrar sesión</span>
        </button>
      </aside>
    </div>
  );
}

function Dashboard({
  records,
  onModule,
  onQuickAdd,
  onRefresh,
  connectionStatus,
  lastSync,
  username,
  showWelcome,
  onDismissWelcome,
  onLogout,
}: {
  records: Record<ModuleKey, RecordItem[]>;
  onModule: (module: ModuleKey) => void;
  onQuickAdd: (module: ModuleKey) => void;
  onRefresh: () => Promise<void>;
  connectionStatus: "demo" | "connecting" | "online" | "offline";
  lastSync: Date | null;
  username: string;
  showWelcome: boolean;
  onDismissWelcome: () => void;
  onLogout: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [hasUnreadNotification, setHasUnreadNotification] = useState(true);
  const [profileOpen, setProfileOpen] = useState(false);
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>("7 días");
  const searchBoxRef = useRef<HTMLDivElement>(null);
  const searchPanelRef = useRef<HTMLDivElement>(null);
  const dashboardToday = new Date();
  const todaySales = records.ventas.filter((item) => {
    const saleDate = parseSaleDate(item.date);
    return saleDate !== null &&
      saleDate.getFullYear() === dashboardToday.getFullYear() &&
      saleDate.getMonth() === dashboardToday.getMonth() &&
      saleDate.getDate() === dashboardToday.getDate();
  });
  const salesTodayTotal = todaySales.reduce((sum, item) => sum + (item.amount ?? 0), 0);
  const chartPoints = buildChartPoints(records.ventas, chartPeriod);
  const chartTotal = chartPoints.reduce((sum, point) => sum + point.value, 0);
  const invoiceCount = records.ventas.length;
  const invoiceTotal = records.ventas.reduce((sum, item) => sum + (item.amount ?? 0), 0);
  const lastInvoice = records.ventas[0];
  const quotes = records.ventas.filter((item) => /cotiz|quote/i.test(`${item.title} ${item.subtitle} ${item.status ?? ""}`));
  const quoteCount = quotes.length;
  const lowStock = records.inventario.filter((item) => item.stock !== undefined && item.stock <= 20);
  const investedCapital = records.inventario.reduce(
    (sum, item) => sum + ((item.stock ?? 0) * (item.price ?? 0)),
    0,
  );
  const profitToday = todaySales.reduce((sum, item) => sum + (item.amount ?? 0) * 0.18, 0);
  const alertCount = lowStock.length + (connectionStatus === "online" ? 0 : 1);
  const paidLoan = records.prestamos.find((item) => /pagado|abono/i.test(`${item.status ?? ""} ${item.subtitle}`));
  const normalizeSearch = (value: string) =>
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLocaleLowerCase("es");
  const normalizedSearch = normalizeSearch(searchQuery);
  const moduleMatches = (Object.keys(moduleInfo) as ModuleKey[])
    .filter((module) =>
      normalizedSearch &&
      normalizeSearch(`${moduleInfo[module].title} ${moduleInfo[module].subtitle}`).includes(normalizedSearch),
    )
    .slice(0, 5);
  const recordMatches = (Object.keys(records) as ModuleKey[])
    .flatMap((module) =>
      records[module].map((item) => ({ ...item, module })),
    )
    .filter((item) =>
      normalizedSearch &&
      normalizeSearch(`${item.title} ${item.subtitle} ${item.status ?? ""}`).includes(normalizedSearch),
    )
    .slice(0, 10);
  const cards = [
    {
      label: "Ventas del día",
      value: money(salesTodayTotal),
      icon: "shopping-cart",
      indicator: `${todaySales.length} ${todaySales.length === 1 ? "venta" : "ventas"} hoy`,
      module: "ventas" as ModuleKey,
      tone: "blue",
    },
    { label: "Capital invertido", value: money(investedCapital), icon: "clipboard-list", indicator: "Inventario valorado", module: "inventario" as ModuleKey, tone: "green" },
    { label: "Productos con stock bajo", value: String(lowStock.length), icon: "package", indicator: lowStock.length ? "Atención requerida" : "Inventario saludable", module: "inventario" as ModuleKey, tone: "gold" },
    { label: "Ganancias del día", value: money(profitToday), icon: "trending-up", indicator: "Utilidad de hoy", module: "ventas" as ModuleKey, tone: "green" },
  ];
  const initials = username.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  const sessionStarted = useRef(new Date()).current;

  useEffect(() => {
    try {
      const savedHistory = JSON.parse(localStorage.getItem("carnes-search-history") ?? "[]") as unknown;
      if (Array.isArray(savedHistory)) {
        setSearchHistory(savedHistory.filter((item): item is string => typeof item === "string").slice(0, 10));
      }
    } catch {
      localStorage.removeItem("carnes-search-history");
    }
  }, []);

  useEffect(() => {
    if (!searchOpen) return;
    const closeSearchFromOutside = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (searchBoxRef.current?.contains(target) || searchPanelRef.current?.contains(target)) return;
      setSearchOpen(false);
    };
    document.addEventListener("pointerdown", closeSearchFromOutside);
    return () => document.removeEventListener("pointerdown", closeSearchFromOutside);
  }, [searchOpen]);

  function saveSearch(term: string) {
    const cleanTerm = term.trim();
    if (!cleanTerm) return;
    setSearchHistory((current) => {
      const next = [cleanTerm, ...current.filter((item) => item.toLocaleLowerCase("es") !== cleanTerm.toLocaleLowerCase("es"))].slice(0, 10);
      localStorage.setItem("carnes-search-history", JSON.stringify(next));
      return next;
    });
  }

  function openSearchResult(module: ModuleKey, term = searchQuery) {
    saveSearch(term);
    setSearchOpen(false);
    setSearchQuery("");
    onModule(module);
  }

  function openGlobalSearch() {
    setSearchOpen(true);
    setAlertsOpen(false);
    setNotificationsOpen(false);
    setProfileOpen(false);
  }

  function submitGlobalSearch() {
    const cleanTerm = searchQuery.trim();
    openGlobalSearch();
    if (!cleanTerm) return;
    saveSearch(cleanTerm);
    setVoiceMessage(
      moduleMatches.length || recordMatches.length
        ? `${moduleMatches.length + recordMatches.length} resultado${moduleMatches.length + recordMatches.length === 1 ? "" : "s"} encontrado${moduleMatches.length + recordMatches.length === 1 ? "" : "s"}.`
        : `No encontramos coincidencias para “${cleanTerm}”.`,
    );
  }

  function startVoiceSearch() {
    openGlobalSearch();
    setVoiceMessage("");
    const voiceWindow = window as VoiceWindow;
    const Recognition = voiceWindow.SpeechRecognition ?? voiceWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceMessage("El dictado por voz no está disponible en esta versión de Safari.");
      return;
    }
    const recognition = new Recognition();
    recognition.lang = "es-MX";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim() ?? "";
      if (transcript) {
        setSearchQuery(transcript);
        saveSearch(transcript);
        setVoiceMessage(`Buscando “${transcript}”`);
      }
    };
    recognition.onerror = () => {
      setVoiceMessage("No pudimos escuchar. Revisa el permiso del micrófono e inténtalo otra vez.");
      setVoiceListening(false);
    };
    recognition.onend = () => setVoiceListening(false);
    try {
      setVoiceListening(true);
      setVoiceMessage("Escuchando…");
      recognition.start();
    } catch {
      setVoiceListening(false);
      setVoiceMessage("El micrófono está ocupado. Inténtalo nuevamente.");
    }
  }

  return (
    <section className="screen dark-screen home-screen">
      {showWelcome && <SecureWelcomeLoader username={username} onComplete={onDismissWelcome} />}

      <header className="home-toolbar">
        <button className="toolbar-menu-button" type="button" onClick={() => { setMenuOpen(!menuOpen); setAlertsOpen(false); setNotificationsOpen(false); }} aria-label="Abrir menú">
          <img src="/icons/menu.svg" alt="" />
        </button>
        <div
          ref={searchBoxRef}
          className="toolbar-search-pill"
          role="search"
          onFocusCapture={openGlobalSearch}
        >
          <button className="toolbar-search-submit" type="button" onClick={submitGlobalSearch} aria-label="Buscar">
            <img src="/icons/search.svg" alt="" />
          </button>
          <input
            value={searchQuery}
            onChange={(event) => {
              setSearchQuery(event.target.value);
              setVoiceMessage("");
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                submitGlobalSearch();
              }
              if (event.key === "Escape") {
                setSearchQuery("");
                setVoiceMessage("");
              }
            }}
            placeholder="Buscar"
            aria-label="Buscar en todo el sistema"
          />
          <button className={voiceListening ? "toolbar-mic listening" : "toolbar-mic"} type="button" onClick={startVoiceSearch} aria-label={voiceListening ? "Escuchando" : "Buscar con micrófono"}>
            <img src="/icons/mic.svg" alt="" />
          </button>
        </div>
        <div className="toolbar-actions">
          <button
            type="button"
            className={`alert-center-button ${alertCount ? "has-alerts" : ""}`}
            onClick={() => {
              setAlertsOpen(!alertsOpen);
              setHasUnreadNotification(false);
              setNotificationsOpen(false);
              setProfileOpen(false);
            }}
            aria-label={`Centro de notificaciones y alertas, ${alertCount} alertas`}
          >
            <img src="/icons/bell.svg" alt="" />
            {(alertCount > 0 || hasUnreadNotification) && <span>{alertCount + (hasUnreadNotification ? 1 : 0)}</span>}
          </button>
          <button
            type="button"
            className="create-center-button"
            onClick={() => {
              setNotificationsOpen(!notificationsOpen);
              setAlertsOpen(false);
              setProfileOpen(false);
            }}
            aria-label="Crear un nuevo registro"
          >
            <span aria-hidden="true">+</span>
          </button>
          <button
            type="button"
            className="profile-avatar"
            onClick={() => {
              setProfileOpen(!profileOpen);
              setAlertsOpen(false);
              setNotificationsOpen(false);
            }}
            aria-label="Abrir perfil"
          >
            {initials}<span className="profile-online-dot" />
          </button>
        </div>
      </header>

      {searchOpen && (
        <div ref={searchPanelRef} className="inline-search-dropdown">
          {voiceMessage && <div className={`voice-search-status ${voiceListening ? "listening" : ""}`}><span />{voiceMessage}</div>}
          {!normalizedSearch ? (
            <>
              <header className="search-history-heading">
                <div><img src="/icons/history.svg" alt="" /><strong>Búsquedas recientes</strong></div>
                {searchHistory.length > 0 && (
                  <button type="button" onClick={() => { setSearchHistory([]); localStorage.removeItem("carnes-search-history"); }}>Borrar</button>
                )}
              </header>
              <div className="search-history-list">
                {searchHistory.map((term) => (
                  <button
                    type="button"
                    key={term}
                    onClick={() => {
                      setSearchQuery(term);
                      setVoiceMessage("");
                      setSearchOpen(true);
                    }}
                  >
                    <img src="/icons/history.svg" alt="" />
                    <span>{term}</span>
                    <b>↗</b>
                  </button>
                ))}
                {searchHistory.length === 0 && <p>Aquí aparecerán tus búsquedas recientes.</p>}
              </div>
            </>
          ) : (
            <div className="inline-search-results">
              {moduleMatches.length > 0 && (
                <div className="search-result-group">
                  <small>Módulos</small>
                  {moduleMatches.map((module) => (
                    <button type="button" key={module} onClick={() => openSearchResult(module)}>
                      <span className="search-result-icon"><img src="/icons/package.svg" alt="" /></span>
                      <span><strong>{moduleInfo[module].title}</strong><small>{moduleInfo[module].subtitle}</small></span>
                      <b>›</b>
                    </button>
                  ))}
                </div>
              )}
              {recordMatches.length > 0 && (
                <div className="search-result-group">
                  <small>Resultados</small>
                  {recordMatches.map((item) => (
                    <button type="button" key={`${item.module}-${item.id}`} onClick={() => openSearchResult(item.module)}>
                      <span className="search-result-icon"><img src="/icons/search.svg" alt="" /></span>
                      <span><strong>{item.title}</strong><small>{moduleInfo[item.module].title} · {item.subtitle}</small></span>
                      <b>›</b>
                    </button>
                  ))}
                </div>
              )}
              {moduleMatches.length === 0 && recordMatches.length === 0 && (
                <div className="inline-search-empty"><strong>Sin resultados</strong><span>No encontramos coincidencias para “{searchQuery}”.</span></div>
              )}
            </div>
          )}
        </div>
      )}

      {menuOpen && (
        <SidebarMenu
          username={username}
          onClose={() => setMenuOpen(false)}
          onModule={(module) => {
            setMenuOpen(false);
            onModule(module);
          }}
          onLogout={() => {
            setMenuOpen(false);
            onLogout();
          }}
        />
      )}
      {alertsOpen && (
        <div className="home-popover alert-center-panel">
          <header><div><strong>Notificaciones y alertas</strong><small>Actividad reciente del sistema</small></div><img src="/icons/bell.svg" alt="" /></header>
          <div className="jelox-login-notification">
            <img src="/jelox-welcome-hd.png" alt="JELOX" />
            <p><strong>Acceso protegido por JELOX</strong><span>{username} inició sesión correctamente.</span><time>Ahora</time></p>
          </div>
          <button type="button" className="notification-event" onClick={() => { setAlertsOpen(false); onModule("inventario"); }}>
            <span><img src="/icons/package.svg" alt="" /></span>
            <span><strong>Inventario actualizado</strong><small>{records.inventario.length} productos sincronizados con el sistema.</small></span>
            <b>›</b>
          </button>
          {paidLoan && (
            <button type="button" className="notification-event payment-event" onClick={() => { setAlertsOpen(false); onModule("prestamos"); }}>
              <span><img src="/icons/hand-coins.svg" alt="" /></span>
              <span><strong>Abono recibido</strong><small>{paidLoan.title} · {paidLoan.subtitle}</small></span>
              <b>›</b>
            </button>
          )}
          {lowStock.map((item) => (
            <button type="button" className="system-alert stock-alert" key={item.id} onClick={() => { setAlertsOpen(false); onModule("inventario"); }}>
              <span><img src="/icons/package.svg" alt="" /></span>
              <span><strong>Stock bajo: {item.title}</strong><small>Quedan {item.stock} unidades. Revisa el inventario.</small></span>
              <b>›</b>
            </button>
          ))}
          {connectionStatus !== "online" && (
            <button type="button" className="system-alert connection-alert" onClick={() => setAlertsOpen(false)}>
              <span><img src="/icons/wifi-off.svg" alt="" /></span>
              <span><strong>Sistema sin sincronización</strong><small>Verifica que el sistema de la PC y la API estén activos.</small></span>
              <b>›</b>
            </button>
          )}
          {connectionStatus === "online" && <div className="alerts-ok"><img src="/icons/circle-check.svg" alt="" /><span><strong>Sistema sincronizado</strong><small>La información se encuentra actualizada.</small></span></div>}
        </div>
      )}
      {notificationsOpen && (
        <div className="create-sheet-backdrop" onPointerDown={(event) => { if (event.target === event.currentTarget) setNotificationsOpen(false); }}>
          <section className="create-menu-panel create-bottom-sheet" role="dialog" aria-modal="true" aria-label="Crear un nuevo registro">
            <span className="bottom-sheet-handle" aria-hidden="true" />
            <header><div><strong>Crear</strong><small>Nuevo registro en el sistema</small></div><span>+</span></header>
            <div className="create-menu-list">
              {creationActions.map((action) => (
                <button type="button" key={action.module} onClick={() => { setNotificationsOpen(false); onQuickAdd(action.module); }}>
                  <span><img src={`/icons/${action.icon}.svg`} alt="" /></span>
                  <span><strong>{action.label}</strong><small>{action.detail}</small></span>
                  <b>›</b>
                </button>
              ))}
            </div>
          </section>
        </div>
      )}
      {profileOpen && (
        <div className="home-popover profile-panel modern-profile-card">
          <header>
            <div><img src="/jelox-welcome-hd.png" alt="" /><strong>Mi cuenta</strong></div>
            <button type="button" onClick={() => setProfileOpen(false)} aria-label="Cerrar perfil"><img src="/icons/x.svg" alt="" /></button>
          </header>
          <div className="profile-identity">
            <div className="profile-hero-avatar">{initials}<span /></div>
            <div>
              <h2>{username}</h2>
              <p>@{username.toLocaleLowerCase("es").replace(/\s+/g, ".")} · Carnes Luévanos</p>
              <em><i /> Activo</em>
            </div>
          </div>
          <div className="profile-data-grid">
            <div><small>Rol</small><strong>Usuario autorizado</strong></div>
            <div><small>Sucursal</small><strong>Principal</strong></div>
            <div><small>Sesión</small><strong>Activa</strong></div>
            <div><small>Último acceso</small><strong>{sessionStarted.toLocaleString("es-MX", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</strong></div>
          </div>
          <button className="profile-primary-action" type="button" onClick={() => { setProfileOpen(false); onModule("configuracion"); }}>Perfil y seguridad</button>
          <button className="profile-secondary-action" type="button" onClick={() => { setProfileOpen(false); onModule("configuracion"); }}>Usuarios y configuración</button>
          <button className="profile-logout-action" type="button" onClick={onLogout}>Cerrar sesión</button>
        </div>
      )}

      <div className="home-intro">
        <div>
          <h1>¡Bienvenido, {username}! <span>👋</span></h1>
          <p>Resumen general de tu negocio</p>
        </div>
        <button
          className={`date-pill home-date sync-tool ${connectionStatus}`}
          type="button"
          onClick={onRefresh}
          disabled={connectionStatus === "connecting"}
          aria-label="Sincronizar ahora con el sistema de la computadora"
        >
          <img src="/icons/refresh-cw.svg" alt="" />
          {connectionStatus === "connecting" ? "Actualizando" : "Sincronizar"}
          <span />
        </button>
      </div>

      <div className="home-metric-grid">
        {cards.map((card) => (
          <button className="home-metric-card" key={card.label} type="button" onClick={() => onModule(card.module)}>
            <span className={`home-metric-icon ${card.tone}`}><img src={`/icons/${card.icon}.svg`} alt="" /></span>
            <small>{card.label}</small>
            <strong>{card.value}</strong>
            <em>{card.indicator}</em>
          </button>
        ))}
      </div>

      <article className="chart-card home-chart-card">
        <div className="section-heading">
          <div>
            <small>Ventas ({chartPeriod === "Hoy" ? "Hoy" : `Últimos ${chartPeriod}`})</small>
            <h2>{money(chartTotal)}</h2>
          </div>
          <button
            className="chart-range-control"
            type="button"
            onClick={() => setChartPeriod((current) => current === "7 días" ? "30 días" : current === "30 días" ? "Hoy" : "7 días")}
            aria-label={`Periodo de la gráfica: ${chartPeriod}. Toca para cambiar`}
          >
            {chartPeriod}⌄
          </button>
        </div>
        <LineChart points={chartPoints} />
        <div className={`home-sync ${connectionStatus}`}>
          <span />
          {connectionStatus === "online"
            ? `Actualizado ${lastSync ? lastSync.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" }) : "ahora"}`
            : connectionStatus === "connecting" ? "Sincronizando" : "Sistema sin conexión"}
        </div>
      </article>

      <article className="billing-home-card">
        <header>
          <div>
            <small>Facturas</small>
            <strong>{invoiceCount ? `${invoiceCount} ${invoiceCount === 1 ? "factura" : "facturas"}` : "Sin facturas"}</strong>
          </div>
          <button type="button" onClick={() => onModule("ventas")}>Administrar facturas</button>
        </header>
        <p>
          {invoiceCount
            ? `Total facturado: ${money(invoiceTotal)}. ${lastInvoice ? `Última: ${lastInvoice.title}` : ""}`
            : "Una vez que crees facturas, estas aparecerán aquí. Envía facturas para recibir pagos en línea."}
        </p>
        <div className="billing-home-actions">
          <button type="button" className="billing-create-link" onClick={() => onQuickAdd("ventas")}>
            Crear nueva factura
          </button>
          <span className={`billing-sync ${connectionStatus}`}>
            <i />
            {connectionStatus === "online" ? "Sincronizado con sistema" : connectionStatus === "connecting" ? "Sincronizando" : "Sin conexión API"}
          </span>
        </div>
      </article>

      <article className="quotes-home-card">
        <header>
          <div>
            <small>Cotizaciones</small>
            <strong>{quoteCount ? `${quoteCount} ${quoteCount === 1 ? "cotización" : "cotizaciones"}` : "Cotizaciones"}</strong>
          </div>
          <button type="button" onClick={() => onModule("ventas")}>Ver todas</button>
        </header>
        <div className="quotes-home-body">
          <span><img src="/icons/receipt-text.svg" alt="" /></span>
          <strong>Cotizaciones</strong>
          <p>Envía cotizaciones a clientes potenciales en minutos, conviértelas en facturas y recibe pagos en línea.</p>
          <button type="button" onClick={() => onQuickAdd("ventas")}>+ Crear cotización</button>
        </div>
      </article>
    </section>
  );
}

function LineChart({ points: dataPoints }: { points?: ChartPoint[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const values = dataPoints?.map((point) => point.value / 1000) ?? [11, 14.5, 23.5, 17, 28, 19, 31];
  const scaleMaximum = Math.max(10, Math.ceil(Math.max(...values, 1) / 10) * 10);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const selected = selectedIndex == null || !dataPoints ? null : dataPoints[selectedIndex];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const draw = () => {
      const bounds = canvas.getBoundingClientRect();
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(bounds.width * pixelRatio);
      canvas.height = Math.round(bounds.height * pixelRatio);
      const context = canvas.getContext("2d");
      if (!context) return;
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      context.clearRect(0, 0, bounds.width, bounds.height);

      const left = 30;
      const right = bounds.width - 5;
      const top = 10;
      const bottom = bounds.height - 25;
      const points = values.map((value, index) => ({
        x: left + (index * (right - left)) / (values.length - 1),
        y: bottom - (value / scaleMaximum) * (bottom - top),
      }));

      context.lineWidth = 1;
      context.strokeStyle = "rgba(133, 155, 172, .13)";
      [0, scaleMaximum / 3, (scaleMaximum * 2) / 3, scaleMaximum].forEach((value) => {
        const y = bottom - (value / scaleMaximum) * (bottom - top);
        context.beginPath();
        context.moveTo(left, y);
        context.lineTo(right, y);
        context.stroke();
      });

      const traceCurve = () => {
        context.beginPath();
        context.moveTo(points[0].x, points[0].y);
        for (let index = 0; index < points.length - 1; index += 1) {
          const current = points[index];
          const next = points[index + 1];
          const middleX = (current.x + next.x) / 2;
          context.quadraticCurveTo(current.x, current.y, middleX, (current.y + next.y) / 2);
        }
        const previous = points[points.length - 2];
        const last = points[points.length - 1];
        context.quadraticCurveTo(previous.x, previous.y, last.x, last.y);
      };

      traceCurve();
      context.lineTo(right, bottom);
      context.lineTo(left, bottom);
      context.closePath();
      const area = context.createLinearGradient(0, top, 0, bottom);
      area.addColorStop(0, "rgba(228, 158, 40, .30)");
      area.addColorStop(1, "rgba(210, 132, 20, .015)");
      context.fillStyle = area;
      context.fill();

      traceCurve();
      context.lineWidth = 2;
      context.strokeStyle = "#e7a13a";
      context.shadowColor = "rgba(231, 161, 58, .48)";
      context.shadowBlur = 6;
      context.stroke();
      context.shadowBlur = 0;

      points.forEach((point) => {
        context.beginPath();
        context.arc(point.x, point.y, 3.2, 0, Math.PI * 2);
        context.fillStyle = "#f2b34e";
        context.fill();
        context.lineWidth = 1.2;
        context.strokeStyle = "#8f5d18";
        context.stroke();
      });
    };

    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [scaleMaximum, values.join("|")]);

  return (
    <div className="line-chart functional-line-chart" role="group" aria-label="Gráfica de ventas. Toca un punto para consultar el importe">
      <div className="chart-y-labels">
        <span>{Math.round(scaleMaximum)}K</span>
        <span>{Math.round((scaleMaximum * 2) / 3)}K</span>
        <span>{Math.round(scaleMaximum / 3)}K</span>
        <span>0</span>
      </div>
      <canvas ref={canvasRef} />
      {dataPoints && (
        <div className="chart-point-controls">
          {dataPoints.map((point, index) => (
            <button
              className={selectedIndex === index ? "active" : ""}
              style={{
                left: `calc(30px + (100% - 35px) * ${index / 6})`,
                top: `calc(10px + (100% - 35px) * ${1 - values[index] / scaleMaximum})`,
              }}
              type="button"
              key={`${point.label}-${index}`}
              onClick={() => setSelectedIndex((current) => current === index ? null : index)}
              aria-label={`${point.detail}: ${money(point.value)}, ${point.operations} operaciones`}
            />
          ))}
        </div>
      )}
      {selected && (
        <div className="chart-point-detail">
          <small>{selected.detail}</small>
          <strong>{money(selected.value)}</strong>
          <span>{selected.operations} {selected.operations === 1 ? "operación" : "operaciones"}</span>
        </div>
      )}
      <div className="chart-labels">
        {(dataPoints ?? [
          { label: "Lun" }, { label: "Mar" }, { label: "Mié" }, { label: "Jue" }, { label: "Vie" }, { label: "Sáb" }, { label: "Dom" },
        ]).map((point, index) => <span key={`${point.label}-${index}`}>{point.label}</span>)}
      </div>
    </div>
  );
}

const adminPermissionOptions: Array<{ key: AdminPermissionKey; label: string; detail: string; icon: string }> = [
  { key: "ventas", label: "Ventas", detail: "Facturar, consultar y cobrar", icon: "receipt-text" },
  { key: "inventario", label: "Inventario", detail: "Productos, precios y existencias", icon: "package" },
  { key: "clientes", label: "Clientes", detail: "Directorio y movimientos", icon: "users" },
  { key: "pedidos", label: "Pedidos", detail: "Solicitudes a proveedores", icon: "clipboard-list" },
  { key: "proveedores", label: "Proveedores", detail: "Directorio de abastecimiento", icon: "truck" },
  { key: "compras", label: "Compras", detail: "Entradas y recepción", icon: "shopping-bag" },
  { key: "rendimiento", label: "Rendimiento", detail: "Indicadores y reportes", icon: "chart-line" },
  { key: "informacion", label: "Información", detail: "Datos generales del negocio", icon: "info" },
  { key: "configuracion", label: "Configuración", detail: "Usuarios y seguridad", icon: "settings" },
];

const rolePresets: Record<string, AdminPermissionKey[]> = {
  super: adminPermissionOptions.map((item) => item.key),
  administrador: adminPermissionOptions.map((item) => item.key),
  ventas: ["ventas", "clientes", "inventario", "informacion"],
  compras: ["compras", "proveedores", "pedidos", "inventario", "informacion"],
  almacen: ["inventario", "pedidos", "proveedores", "informacion"],
  usuario: ["informacion"],
};

function permissionsForRole(role: string) {
  const allowed = new Set(rolePresets[role] ?? rolePresets.usuario);
  return Object.fromEntries(
    adminPermissionOptions.map((permission) => [permission.key, allowed.has(permission.key)]),
  ) as Record<AdminPermissionKey, boolean>;
}

const defaultCommercialInfo: CommercialInfo = {
  name: "Carnes Luévanos",
  legalName: "Carnes Luévanos",
  taxId: "J-00000000-0",
  phone: "+52 87 1503 4671",
  email: "info@carnesluevanos.com",
  address: "Torreón, Coah.",
  currency: "USD",
};

function ModuleHub({
  onModule,
  username,
  connectionStatus,
  callApi,
  usersOnly = false,
}: {
  onModule: (module: ModuleKey) => void;
  username: string;
  connectionStatus: "demo" | "connecting" | "online" | "offline";
  callApi: (path: string, options?: RequestInit) => Promise<unknown>;
  usersOnly?: boolean;
}) {
  const [section, setSection] = useState<"permissions" | "commercial" | "modules">("permissions");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [company, setCompany] = useState<CommercialInfo>(defaultCommercialInfo);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [creatingUser, setCreatingUser] = useState(false);
  const [newUser, setNewUser] = useState({
    name: "",
    username: "",
    password: "",
    confirmPassword: "",
    role: "usuario",
    branch: "",
    employeeNumber: "",
    permissions: permissionsForRole("usuario"),
  });
  const selectedUser = users.find((user) => user.id === selectedUserId) ?? users[0];
  const protectedUser = selectedUser?.role === "super";

  useEffect(() => {
    let active = true;
    async function loadAdmin() {
      setLoading(true);
      try {
        const payload = await callApi(`/api/mobile/admin?actor=${encodeURIComponent(username)}`) as AdminPayload;
        if (!active) return;
        setUsers(payload.users ?? []);
        setSelectedUserId((current) => current ?? payload.users?.[0]?.id ?? null);
        setCompany({ ...defaultCommercialInfo, ...(payload.company ?? {}) });
        setNotice("");
      } catch (error) {
        if (active) setNotice(error instanceof Error ? error.message : "No se pudo cargar la administración");
      } finally {
        if (active) setLoading(false);
      }
    }
    loadAdmin();
    return () => { active = false; };
  }, [callApi, username]);

  function updateSelectedUser(update: Partial<AdminUser>) {
    if (!selectedUser) return;
    setUsers((current) => current.map((user) => user.id === selectedUser.id ? { ...user, ...update } : user));
  }

  function selectRole(role: string) {
    updateSelectedUser({
      role,
      permissions: permissionsForRole(role),
    });
  }

  function resetNewUser() {
    setNewUser({
      name: "",
      username: "",
      password: "",
      confirmPassword: "",
      role: "usuario",
      branch: "",
      employeeNumber: "",
      permissions: permissionsForRole("usuario"),
    });
  }

  async function createUser(event: FormEvent) {
    event.preventDefault();
    setNotice("");
    if (newUser.password.length < 10) {
      setNotice("La contraseña debe tener al menos 10 caracteres.");
      return;
    }
    if (newUser.password !== newUser.confirmPassword) {
      setNotice("Las contraseñas no coinciden.");
      return;
    }
    setSaving(true);
    try {
      const created = await callApi("/api/mobile/admin/users", {
        method: "POST",
        body: JSON.stringify({
          actor: username,
          name: newUser.name,
          username: newUser.username,
          password: newUser.password,
          role: newUser.role,
          branch: newUser.branch,
          employeeNumber: newUser.employeeNumber,
          permissions: newUser.permissions,
        }),
      }) as AdminUser;
      setUsers((current) => [...current, created]);
      setSelectedUserId(created.id);
      setCreatingUser(false);
      resetNewUser();
      setNotice(`Usuario ${created.name} creado con sus permisos.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "No se pudo crear el usuario");
    } finally {
      setSaving(false);
    }
  }

  async function saveUserAccess() {
    if (!selectedUser || protectedUser) return;
    setSaving(true);
    setNotice("");
    try {
      await callApi(`/api/mobile/admin/users/${selectedUser.id}`, {
        method: "PUT",
        body: JSON.stringify({ actor: username, role: selectedUser.role, permissions: selectedUser.permissions }),
      });
      setNotice(`Permisos de ${selectedUser.name} sincronizados con el sistema.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "No se pudieron guardar los permisos");
    } finally {
      setSaving(false);
    }
  }

  async function saveCompany() {
    setSaving(true);
    setNotice("");
    try {
      await callApi("/api/mobile/admin/company", {
        method: "PUT",
        body: JSON.stringify({ actor: username, ...company }),
      });
      setNotice("Información comercial actualizada en el sistema.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "No se pudo actualizar la información");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="screen dark-screen admin-center-screen">
      <header className="admin-center-heading">
        <span><img src={usersOnly ? "/icons/user-plus.svg" : "/icons/menu.svg"} alt="" /></span>
        <div><small>Centro de gestión</small><h1>{usersOnly ? "Usuarios" : "Administrar"}</h1><p>{usersOnly ? "Cuentas, roles y permisos del sistema" : "Usuarios, seguridad e información comercial"}</p></div>
        <i className={`admin-live-dot ${connectionStatus}`}>{connectionStatus === "online" ? "En línea" : "Sin conexión"}</i>
      </header>

      {!usersOnly && <nav className="admin-tabs" aria-label="Secciones de administración">
        <button className={section === "permissions" ? "active" : ""} onClick={() => setSection("permissions")}><img src="/icons/circle-check.svg" alt="" />Roles</button>
        <button className={section === "commercial" ? "active" : ""} onClick={() => setSection("commercial")}><img src="/icons/info.svg" alt="" />Empresa</button>
        <button className={section === "modules" ? "active" : ""} onClick={() => setSection("modules")}><img src="/icons/package.svg" alt="" />Módulos</button>
      </nav>}

      {notice && <div className={`admin-notice ${/sincroniz|actualizada|creado/i.test(notice) ? "success" : ""}`}><span>i</span><p>{notice}</p></div>}

      {section === "permissions" && (
        <div className="admin-permissions">
          <div className="admin-section-heading">
            <div><small>Control de acceso</small><h2>Usuarios y permisos</h2></div>
            <div className="admin-user-actions"><b>{users.length} usuarios</b><button type="button" onClick={() => setCreatingUser((current) => !current)}><img src="/icons/user-plus.svg" alt="" />Agregar</button></div>
          </div>
          {creatingUser && (
            <form className="admin-create-user-card" onSubmit={createUser}>
              <header><div><small>Nueva cuenta</small><h3>Agregar usuario</h3></div><button type="button" onClick={() => { setCreatingUser(false); resetNewUser(); }} aria-label="Cancelar">×</button></header>
              <div className="admin-create-fields">
                <label className="wide"><span>Nombre completo</span><input value={newUser.name} onChange={(event) => setNewUser({ ...newUser, name: event.target.value })} autoComplete="name" required /></label>
                <label><span>Usuario</span><input value={newUser.username} onChange={(event) => setNewUser({ ...newUser, username: event.target.value })} autoCapitalize="none" autoComplete="off" minLength={3} required /></label>
                <label><span>Rol</span><select value={newUser.role} onChange={(event) => setNewUser({ ...newUser, role: event.target.value, permissions: permissionsForRole(event.target.value) })}><option value="administrador">Administrador</option><option value="ventas">Ventas</option><option value="compras">Compras</option><option value="almacen">Almacén</option><option value="usuario">Usuario</option></select></label>
                <label><span>Sucursal</span><input value={newUser.branch} onChange={(event) => setNewUser({ ...newUser, branch: event.target.value })} /></label>
                <label><span>Número de empleado</span><input value={newUser.employeeNumber} onChange={(event) => setNewUser({ ...newUser, employeeNumber: event.target.value })} /></label>
                <label><span>Contraseña temporal</span><input type="password" value={newUser.password} onChange={(event) => setNewUser({ ...newUser, password: event.target.value })} autoComplete="new-password" minLength={10} required /></label>
                <label><span>Confirmar contraseña</span><input type="password" value={newUser.confirmPassword} onChange={(event) => setNewUser({ ...newUser, confirmPassword: event.target.value })} autoComplete="new-password" minLength={10} required /></label>
              </div>
              <div className="permission-list compact">
                {adminPermissionOptions.map((permission) => (
                  <label key={permission.key}>
                    <span className="permission-icon"><img src={`/icons/${permission.icon}.svg`} alt="" /></span>
                    <span><strong>{permission.label}</strong><small>{permission.detail}</small></span>
                    <input type="checkbox" checked={newUser.permissions[permission.key]} onChange={(event) => setNewUser({ ...newUser, permissions: { ...newUser.permissions, [permission.key]: event.target.checked } })} />
                    <i />
                  </label>
                ))}
              </div>
              <button className="admin-save-button" disabled={saving}><img src="/icons/user-plus.svg" alt="" />{saving ? "Creando usuario…" : "Crear usuario y asignar permisos"}</button>
            </form>
          )}
          {loading ? (
            <div className="admin-loading"><span /><p>Cargando usuarios del sistema…</p></div>
          ) : users.length === 0 ? (
            <div className="admin-empty"><img src="/icons/users.svg" alt="" /><strong>Sin usuarios disponibles</strong><p>Comprueba que la API de la PC esté abierta.</p></div>
          ) : (
            <>
              <div className="admin-user-strip">
                {users.map((user) => (
                  <button key={user.id} className={selectedUser?.id === user.id ? "active" : ""} onClick={() => setSelectedUserId(user.id)}>
                    <span>{user.name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</span>
                    <div><strong>{user.name}</strong><small>@{user.username}</small></div>
                    <i className={user.status.toLowerCase()} />
                  </button>
                ))}
              </div>

              {selectedUser && (
                <article className="admin-access-card">
                  <header>
                    <span>{selectedUser.name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</span>
                    <div><small>Cuenta seleccionada</small><h3>{selectedUser.name}</h3><p>{selectedUser.branch || "Sucursal sin asignar"} · {selectedUser.status}</p></div>
                    {protectedUser && <b>Protegida</b>}
                  </header>
                  <label className="admin-role-select">
                    <span>Rol operativo<small>Aplica una plantilla y permite ajustes individuales</small></span>
                    <select value={selectedUser.role} disabled={protectedUser} onChange={(event) => selectRole(event.target.value)}>
                      <option value="super">Superadministrador</option>
                      <option value="administrador">Administrador</option>
                      <option value="ventas">Ventas</option>
                      <option value="compras">Compras</option>
                      <option value="almacen">Almacén</option>
                      <option value="usuario">Usuario</option>
                    </select>
                  </label>
                  <div className="permission-list">
                    {adminPermissionOptions.map((permission) => (
                      <label key={permission.key}>
                        <span className="permission-icon"><img src={`/icons/${permission.icon}.svg`} alt="" /></span>
                        <span><strong>{permission.label}</strong><small>{permission.detail}</small></span>
                        <input
                          type="checkbox"
                          disabled={protectedUser}
                          checked={protectedUser || Boolean(selectedUser.permissions?.[permission.key])}
                          onChange={(event) => updateSelectedUser({ permissions: { ...selectedUser.permissions, [permission.key]: event.target.checked } })}
                        />
                        <i />
                      </label>
                    ))}
                  </div>
                  <button className="admin-save-button" disabled={saving || protectedUser} onClick={saveUserAccess}>
                    <img src="/icons/circle-check.svg" alt="" />
                    {protectedUser ? "Acceso total protegido" : saving ? "Sincronizando…" : "Guardar rol y permisos"}
                  </button>
                </article>
              )}
            </>
          )}
        </div>
      )}

      {section === "commercial" && (
        <form className="commercial-card" onSubmit={(event) => { event.preventDefault(); saveCompany(); }}>
          <div className="commercial-brand">
            <img src="/logo-luevanos.png" alt="Carnes Luévanos" />
            <div><small>Perfil comercial</small><h2>{company.name}</h2><p>Información utilizada por todo el sistema</p></div>
          </div>
          <div className="commercial-fields">
            <label><span>Nombre comercial</span><input value={company.name} onChange={(event) => setCompany({ ...company, name: event.target.value })} /></label>
            <label><span>Razón social</span><input value={company.legalName} onChange={(event) => setCompany({ ...company, legalName: event.target.value })} /></label>
            <label><span>RFC / RIF</span><input value={company.taxId} onChange={(event) => setCompany({ ...company, taxId: event.target.value })} /></label>
            <label><span>Teléfono</span><input inputMode="tel" value={company.phone} onChange={(event) => setCompany({ ...company, phone: event.target.value })} /></label>
            <label className="wide"><span>Correo comercial</span><input inputMode="email" value={company.email} onChange={(event) => setCompany({ ...company, email: event.target.value })} /></label>
            <label className="wide"><span>Dirección</span><textarea rows={3} value={company.address} onChange={(event) => setCompany({ ...company, address: event.target.value })} /></label>
            <label className="wide"><span>Moneda principal</span><select value={company.currency} onChange={(event) => setCompany({ ...company, currency: event.target.value })}><option value="MXN">MXN · Peso mexicano</option><option value="USD">USD · Dólar estadounidense</option></select></label>
          </div>
          <div className="commercial-security"><img src="/icons/circle-check.svg" alt="" /><p><strong>Datos centralizados</strong><small>Los cambios se reflejan en la información comercial del sistema de escritorio.</small></p></div>
          <button className="admin-save-button" disabled={saving}><img src="/icons/circle-check.svg" alt="" />{saving ? "Guardando…" : "Guardar información comercial"}</button>
        </form>
      )}

      {section === "modules" && (
        <div className="module-grid">
          {(Object.keys(moduleInfo) as ModuleKey[]).map((key) => (
            <button className="module-card" key={key} onClick={() => onModule(key)}>
              <span><img src={`/icons/${sidebarItems.find((item) => item.module === key)?.icon ?? "settings"}.svg`} alt="" /></span>
              <strong>{moduleInfo[key].title}</strong>
              <small>{moduleInfo[key].subtitle}</small>
              <b>›</b>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function ReportsCenter({
  records,
  username,
  connectionStatus,
  onModule,
  onQuickAdd,
  onLogout,
}: {
  records: Record<ModuleKey, RecordItem[]>;
  username: string;
  connectionStatus: "demo" | "connecting" | "online" | "offline";
  onModule: (module: ModuleKey) => void;
  onQuickAdd: (module: ModuleKey) => void;
  onLogout: () => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [reportModule, setReportModule] = useState<ModuleKey>("ventas");
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState(today);
  const [generated, setGenerated] = useState(false);
  const [generatedAt, setGeneratedAt] = useState<Date | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [reportVoiceListening, setReportVoiceListening] = useState(false);
  const reportOptions: Array<{ module: ModuleKey; label: string }> = [
    { module: "ventas", label: "Ventas diarias" },
    { module: "compras", label: "Compras" },
    { module: "inventario", label: "Inventario y existencias" },
    { module: "clientes", label: "Directorio de clientes" },
    { module: "proveedores", label: "Directorio de proveedores" },
    { module: "pedidos", label: "Pedidos a proveedores" },
    { module: "prestamos", label: "Préstamos y abonos" },
    { module: "nominas", label: "Nóminas" },
  ];
  const selectedLabel = reportOptions.find((option) => option.module === reportModule)?.label ?? "Reporte";
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T23:59:59`);
  const reportRows = records[reportModule].filter((item) => {
    const itemDate = parseSaleDate(item.date);
    if (!itemDate) return reportModule !== "ventas" && reportModule !== "compras";
    return itemDate >= start && itemDate <= end;
  });
  const reportTotal = reportRows.reduce((sum, item) => sum + (item.amount ?? item.price ?? 0), 0);
  const reportUnits = reportRows.reduce((sum, item) => sum + (item.stock ?? 0), 0);
  const reportAverage = reportRows.length ? reportTotal / reportRows.length : 0;
  const lowStock = records.inventario.filter((item) => item.stock !== undefined && item.stock <= 20);
  const initials = username.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  const normalizeReportSearch = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es").trim();
  const normalizedReportSearch = normalizeReportSearch(searchQuery);
  const reportModuleMatches = (Object.keys(moduleInfo) as ModuleKey[]).filter((key) => normalizedReportSearch && normalizeReportSearch(`${moduleInfo[key].title} ${moduleInfo[key].subtitle}`).includes(normalizedReportSearch)).slice(0, 4);
  const reportRecordMatches = (Object.keys(records) as ModuleKey[])
    .flatMap((key) => records[key].map((item) => ({ ...item, module: key })))
    .filter((item) => normalizedReportSearch && normalizeReportSearch(`${item.title} ${item.subtitle} ${item.status ?? ""}`).includes(normalizedReportSearch))
    .slice(0, 6);

  function closeReportsToolbar() {
    setMenuOpen(false);
    setSearchOpen(false);
    setAlertsOpen(false);
    setCreateOpen(false);
    setProfileOpen(false);
  }

  function startReportVoiceSearch() {
    const voiceWindow = window as VoiceWindow;
    const Recognition = voiceWindow.SpeechRecognition ?? voiceWindow.webkitSpeechRecognition;
    if (!Recognition) return;
    const recognition = new Recognition();
    recognition.lang = "es-MX";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim() ?? "";
      if (transcript) {
        setSearchQuery(transcript);
        setSearchOpen(true);
      }
    };
    recognition.onerror = () => setReportVoiceListening(false);
    recognition.onend = () => setReportVoiceListening(false);
    try {
      setReportVoiceListening(true);
      recognition.start();
    } catch {
      setReportVoiceListening(false);
    }
  }

  function generateReport() {
    setGenerated(true);
    setGeneratedAt(new Date());
  }

  function printReport(pdfMode = false) {
    if (!generated) generateReport();
    const previousTitle = document.title;
    document.title = `${selectedLabel}-${startDate}-${endDate}`;
    document.body.classList.add("report-print-mode");
    window.setTimeout(() => {
      window.print();
      document.body.classList.remove("report-print-mode");
      document.title = previousTitle;
    }, pdfMode ? 180 : 80);
  }

  return (
    <section className="screen dark-screen reports-screen">
      <header className="home-toolbar reports-toolbar">
        <button className="toolbar-menu-button" type="button" onClick={() => { const next = !menuOpen; closeReportsToolbar(); setMenuOpen(next); }} aria-label="Abrir menú"><img src="/icons/menu.svg" alt="" /></button>
        <div className="toolbar-search-pill" role="search" onFocusCapture={() => { closeReportsToolbar(); setSearchOpen(true); }}>
          <button className="toolbar-search-submit" type="button" onClick={() => setSearchOpen(true)} aria-label="Buscar en todo el sistema"><img src="/icons/search.svg" alt="" /></button>
          <input value={searchQuery} onChange={(event) => { setSearchQuery(event.target.value); setSearchOpen(true); }} placeholder="Buscar" aria-label="Buscar en todo el sistema" />
          <button className={reportVoiceListening ? "toolbar-mic listening" : "toolbar-mic"} type="button" onClick={startReportVoiceSearch} aria-label="Buscar con micrófono"><img src="/icons/mic.svg" alt="" /></button>
        </div>
        <div className="toolbar-actions">
          <button type="button" className={`alert-center-button ${lowStock.length ? "has-alerts" : ""}`} onClick={() => { const next = !alertsOpen; closeReportsToolbar(); setAlertsOpen(next); }} aria-label="Notificaciones y alertas"><img src="/icons/bell.svg" alt="" />{lowStock.length > 0 && <span>{lowStock.length}</span>}</button>
          <button type="button" className="create-center-button" onClick={() => { const next = !createOpen; closeReportsToolbar(); setCreateOpen(next); }} aria-label="Crear un registro"><span>+</span></button>
          <button type="button" className="profile-avatar" onClick={() => { const next = !profileOpen; closeReportsToolbar(); setProfileOpen(next); }} aria-label="Abrir perfil">{initials}<span className="profile-online-dot" /></button>
        </div>
      </header>

      {searchOpen && (
        <div className="inline-search-dropdown reports-search-dropdown">
          {!normalizedReportSearch ? <div className="inline-search-empty"><strong>Búsqueda general</strong><span>Busca clientes, productos, ventas o módulos.</span></div> : (
            <div className="inline-search-results">
              {reportModuleMatches.length > 0 && <div className="search-result-group"><small>Módulos</small>{reportModuleMatches.map((key) => <button type="button" key={key} onClick={() => { closeReportsToolbar(); onModule(key); }}><span className="search-result-icon"><img src="/icons/package.svg" alt="" /></span><span><strong>{moduleInfo[key].title}</strong><small>{moduleInfo[key].subtitle}</small></span><b>›</b></button>)}</div>}
              {reportRecordMatches.length > 0 && <div className="search-result-group"><small>Resultados</small>{reportRecordMatches.map((item) => <button type="button" key={`${item.module}-${item.id}`} onClick={() => { closeReportsToolbar(); onModule(item.module); }}><span className="search-result-icon"><img src="/icons/search.svg" alt="" /></span><span><strong>{item.title}</strong><small>{moduleInfo[item.module].title} · {item.subtitle}</small></span><b>›</b></button>)}</div>}
              {!reportModuleMatches.length && !reportRecordMatches.length && <div className="inline-search-empty"><strong>Sin resultados</strong><span>No encontramos “{searchQuery}”.</span></div>}
            </div>
          )}
        </div>
      )}
      {menuOpen && <SidebarMenu username={username} onClose={() => setMenuOpen(false)} onModule={(key) => { closeReportsToolbar(); onModule(key); }} onLogout={onLogout} />}
      {alertsOpen && <div className="home-popover alert-center-panel reports-toolbar-panel"><header><div><strong>Notificaciones y alertas</strong><small>Actividad reciente</small></div><img src="/icons/bell.svg" alt="" /></header>{lowStock.map((item) => <button type="button" className="system-alert stock-alert" key={item.id} onClick={() => { closeReportsToolbar(); onModule("inventario"); }}><span><img src="/icons/package.svg" alt="" /></span><span><strong>Stock bajo: {item.title}</strong><small>Quedan {item.stock} unidades.</small></span><b>›</b></button>)}<div className="alerts-ok"><img src="/icons/circle-check.svg" alt="" /><span><strong>{connectionStatus === "online" ? "Reportes sincronizados" : "Conexión limitada"}</strong><small>{connectionStatus === "online" ? "Datos actualizados desde el sistema." : "Abre el sistema de la computadora."}</small></span></div></div>}
      {profileOpen && <div className="home-popover module-toolbar-profile reports-toolbar-panel"><span className="profile-avatar large">{initials}</span><strong>{username}</strong><small>Usuario autorizado · Reportes</small><button type="button" onClick={() => { closeReportsToolbar(); onModule("configuracion"); }}>Perfil y seguridad</button><button className="logout" type="button" onClick={onLogout}>Cerrar sesión</button></div>}
      {createOpen && (
        <div className="create-sheet-backdrop" onPointerDown={(event) => { if (event.target === event.currentTarget) setCreateOpen(false); }}>
          <section className="create-menu-panel create-bottom-sheet" role="dialog" aria-modal="true" aria-label="Crear un registro"><span className="bottom-sheet-handle" /><header><div><strong>Crear</strong><small>Nuevo registro en el sistema</small></div><span>+</span></header><div className="create-menu-list">{creationActions.map((action) => <button type="button" key={action.module} onClick={() => { setCreateOpen(false); onQuickAdd(action.module); }}><span><img src={`/icons/${action.icon}.svg`} alt="" /></span><span><strong>{action.label}</strong><small>{action.detail}</small></span><b>›</b></button>)}</div></section>
        </div>
      )}

      <header className="reports-hero">
        <span><img src="/icons/chart-line.svg" alt="" /></span>
        <div><small>Inteligencia del negocio</small><h1>Reportes</h1><p>Genera, revisa y comparte información del sistema.</p></div>
      </header>

      <article className="report-options-card">
        <div className="report-section-title"><span><img src="/icons/clipboard-list.svg" alt="" /></span><div><strong>Opciones de reporte</strong><small>Configura la información que necesitas</small></div></div>
        <label>
          Tipo de reporte
          <select value={reportModule} onChange={(event) => { setReportModule(event.target.value as ModuleKey); setGenerated(false); }}>
            {reportOptions.map((option) => <option value={option.module} key={option.module}>{option.label}</option>)}
          </select>
        </label>
        <div className="report-date-grid">
          <label>Fecha inicial<input type="date" value={startDate} max={endDate} onChange={(event) => { setStartDate(event.target.value); setGenerated(false); }} /></label>
          <label>Fecha final<input type="date" value={endDate} min={startDate} onChange={(event) => { setEndDate(event.target.value); setGenerated(false); }} /></label>
        </div>
        <div className="report-action-grid">
          <button className="generate" type="button" onClick={generateReport}><img src="/icons/chart-line.svg" alt="" />Generar</button>
          <button className="pdf" type="button" onClick={() => printReport(true)}><img src="/icons/receipt-text.svg" alt="" />Exportar PDF</button>
          <button className="print" type="button" onClick={() => printReport(false)}><img src="/icons/clipboard-list.svg" alt="" />Imprimir</button>
        </div>
      </article>

      <article className={`report-preview ${generated ? "ready" : ""}`}>
        {!generated ? (
          <div className="report-empty-preview">
            <span><img src="/icons/chart-line.svg" alt="" /></span>
            <strong>Vista previa del reporte</strong>
            <p>Selecciona el tipo y las fechas, luego toca Generar.</p>
          </div>
        ) : (
          <>
            <header className="report-document-heading">
              <img src="/logo-luevanos.png" alt="Carnes Luévanos" />
              <div><small>Carnes Luévanos · Sistema Administrativo</small><h2>{selectedLabel}</h2><p>{startDate} — {endDate}</p></div>
              <span>JELOX<br />STUDIO</span>
            </header>
            <div className="report-summary-grid">
              <article><small>Total</small><strong>{money(reportTotal)}</strong></article>
              <article><small>Registros</small><strong>{reportRows.length}</strong></article>
              <article><small>{reportModule === "inventario" ? "Existencias" : "Promedio"}</small><strong>{reportModule === "inventario" ? reportUnits : money(reportAverage)}</strong></article>
            </div>
            <div className="report-document-meta"><span>Generado por {username}</span><span>{generatedAt?.toLocaleString("es-MX")}</span></div>
            <div className="report-table">
              <header><span>Registro</span><span>Detalle</span><span>Estado</span><span>Importe</span></header>
              {reportRows.map((item) => (
                <div key={item.id}><strong>{item.title}</strong><span>{item.subtitle || "Sin detalle"}</span><em>{item.status ?? "Registrado"}</em><b>{item.amount != null ? money(item.amount) : item.stock != null ? `${item.stock} u.` : "—"}</b></div>
              ))}
              {!reportRows.length && <p>No existen registros para el periodo seleccionado.</p>}
            </div>
            <footer>Reporte protegido y generado por JELOX Studio · {new Date().getFullYear()}</footer>
          </>
        )}
      </article>
    </section>
  );
}

function JeloxAiCenter({
  username,
  records,
  connectionStatus,
  onQuickAdd,
  callApi,
}: {
  username: string;
  records: Record<ModuleKey, RecordItem[]>;
  connectionStatus: "demo" | "connecting" | "online" | "offline";
  onQuickAdd: (module: ModuleKey) => void;
  callApi: (path: string, options?: RequestInit) => Promise<unknown>;
}) {
  const [createOpen, setCreateOpen] = useState(false);
  const [messages, setMessages] = useState<Array<{ user: boolean; text: string }>>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const initials = username.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  const lowStock = records.inventario.filter((item) => item.stock !== undefined && item.stock <= 20);

  async function sendMessage(value = text) {
    const question = value.trim();
    if (!question || busy) return;
    setText("");
    setMessages((current) => [...current, { user: true, text: question }]);
    setBusy(true);
    try {
      const response = await callApi("/api/mobile/jelox/chat", { method: "POST", body: JSON.stringify({ message: question }) }) as { answer?: string };
      setMessages((current) => [...current, { user: false, text: response.answer ?? "He terminado de analizar tu solicitud." }]);
    } catch {
      const fallback = /venta/i.test(question)
        ? `Hoy hay ${records.ventas.length} operaciones disponibles para analizar. Puedes consultar Reportes para ver el detalle.`
        : /stock|inventario/i.test(question)
          ? `Encontré ${lowStock.length} producto${lowStock.length === 1 ? "" : "s"} con stock bajo.`
          : "Puedo ayudarte con ventas, inventario, clientes, compras, pedidos y reportes cuando el sistema esté conectado.";
      setMessages((current) => [...current, { user: false, text: fallback }]);
    } finally {
      setBusy(false);
    }
  }

  function startListening() {
    const voiceWindow = window as VoiceWindow;
    const Recognition = voiceWindow.SpeechRecognition ?? voiceWindow.webkitSpeechRecognition;
    if (!Recognition) return;
    const recognition = new Recognition();
    recognition.lang = "es-MX";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim() ?? "";
      if (transcript) setText(transcript);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    setListening(true);
    recognition.start();
  }

  return (
    <section className="screen dark-screen jelox-ai-screen jelox-conversation-screen">
      {createOpen && (
        <div className="create-sheet-backdrop" onPointerDown={(event) => { if (event.target === event.currentTarget) setCreateOpen(false); }}>
          <section className="create-menu-panel create-bottom-sheet" role="dialog" aria-modal="true" aria-label="Crear un registro">
            <span className="bottom-sheet-handle" />
            <header><div><strong>Crear con JELOX</strong><small>Nuevo registro en el sistema</small></div><span>+</span></header>
            <div className="create-menu-list">{creationActions.map((action) => <button type="button" key={action.module} onClick={() => { setCreateOpen(false); onQuickAdd(action.module); }}><span><img src={`/icons/${action.icon}.svg`} alt="" /></span><span><strong>{action.label}</strong><small>{action.detail}</small></span><b>›</b></button>)}</div>
          </section>
        </div>
      )}

      <header className="jelox-agent-heading">
        <div><img src="/jelox-welcome-hd.png" alt="JELOX IA" /><span><strong>JELOX IA</strong><small><i /> Asistente activo</small></span></div>
        <span className={`jelox-agent-connection ${connectionStatus}`}>{connectionStatus === "online" ? "En línea" : "Local"}</span>
      </header>

      <div className="jelox-conversation">
        {messages.length === 0 ? (
          <div className="jelox-empty-conversation">
            <span className="jelox-orb"><img src="/jelox-welcome-hd.png" alt="" /></span>
            <h1>Hola, soy <b>JELOX IA</b></h1>
            <h2>Tu especialista en administración y análisis</h2>
            <p>Estoy aquí para ayudarte a revisar ventas, inventario, clientes, reportes y ofrecerte funciones útiles.</p>
            <div className="jelox-prompt-chips">
              {["Resumen de hoy", "Revisar stock", "Analizar ventas"].map((prompt) => <button type="button" key={prompt} onClick={() => sendMessage(prompt)}>{prompt}</button>)}
            </div>
          </div>
        ) : (
          <div className="jelox-screen-messages">
            {messages.map((message, index) => <div className={message.user ? "user" : "assistant"} key={`${index}-${message.text}`}><span>{message.user ? initials : "J"}</span><p>{message.text}</p></div>)}
            {busy && <div className="assistant typing"><span>J</span><p><i /><i /><i /></p></div>}
          </div>
        )}
      </div>

      <form className="jelox-workspace-composer" onSubmit={(event) => { event.preventDefault(); sendMessage(); }}>
        <input value={text} onChange={(event) => setText(event.target.value)} placeholder="Pregúntame lo que quieras" aria-label="Mensaje para JELOX IA" />
        <div>
          <button className="add" type="button" onClick={() => setCreateOpen(true)} aria-label="Crear con JELOX">+</button>
          <button className={listening ? "mic listening" : "mic"} type="button" onClick={startListening} aria-label="Dictar mensaje"><img src="/icons/mic.svg" alt="" /></button>
          <button className="send" disabled={!text.trim() || busy} aria-label="Enviar mensaje"><span /><span /><span /></button>
        </div>
      </form>
      <p className="jelox-disclaimer">JELOX puede cometer errores. Verifica la información importante del sistema.</p>
    </section>
  );
}

function NotificationInbox({
  records,
  connectionStatus,
  onModule,
}: {
  records: Record<ModuleKey, RecordItem[]>;
  connectionStatus: "demo" | "connecting" | "online" | "offline";
  onModule: (module: ModuleKey) => void;
}) {
  const lowStock = records.inventario.filter((item) => item.stock !== undefined && item.stock <= 20);
  const paidLoan = records.prestamos.find((item) => /pagado|abono/i.test(`${item.status ?? ""} ${item.subtitle}`));
  return (
    <section className="screen dark-screen inbox-screen">
      <header className="inbox-heading"><span><img src="/icons/mail.svg" alt="" /></span><div><small>Centro de comunicaciones</small><h1>Bandeja de entrada</h1><p>Alertas y movimientos importantes.</p></div></header>
      <div className="inbox-list">
        <button type="button" onClick={() => onModule("inventario")}><span><img src="/icons/package.svg" alt="" /></span><div><strong>Inventario actualizado</strong><small>{records.inventario.length} productos sincronizados.</small></div><time>Ahora</time></button>
        {paidLoan && <button type="button" onClick={() => onModule("prestamos")}><span className="green"><img src="/icons/hand-coins.svg" alt="" /></span><div><strong>Abono recibido</strong><small>{paidLoan.title} · {paidLoan.subtitle}</small></div><time>Hoy</time></button>}
        {lowStock.map((item) => <button type="button" key={item.id} onClick={() => onModule("inventario")}><span className="gold"><img src="/icons/triangle-alert.svg" alt="" /></span><div><strong>Stock bajo: {item.title}</strong><small>Quedan {item.stock} unidades.</small></div><time>Alerta</time></button>)}
        <article className={`inbox-connection ${connectionStatus}`}><span><i /></span><div><strong>{connectionStatus === "online" ? "Sistema conectado" : "Sin conexión con la API"}</strong><small>{connectionStatus === "online" ? "Los datos se actualizan en tiempo real." : "Abre el sistema de la computadora para sincronizar."}</small></div></article>
      </div>
    </section>
  );
}

function ModuleView({
  module,
  records,
  allRecords,
  onBack,
  onAdd,
  onDelete,
  connectionStatus,
  username,
  onModule,
  onQuickAdd,
  onLogout,
}: {
  module: ModuleKey;
  records: RecordItem[];
  allRecords: Record<ModuleKey, RecordItem[]>;
  onBack?: () => void;
  onAdd: () => void;
  onDelete: (id: number) => void;
  connectionStatus: "demo" | "connecting" | "online" | "offline";
  username: string;
  onModule: (module: ModuleKey) => void;
  onQuickAdd: (module: ModuleKey) => void;
  onLogout: () => void;
}) {
  const [filter, setFilter] = useState("Todos");
  const [query, setQuery] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [inventoryMenuOpen, setInventoryMenuOpen] = useState(false);
  const [selectedInventoryItem, setSelectedInventoryItem] = useState<RecordItem | null>(null);
  const [voiceListening, setVoiceListening] = useState(false);
  const [globalSearchOpen, setGlobalSearchOpen] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [searchMessage, setSearchMessage] = useState("");
  const moduleSearchRef = useRef<HTMLInputElement>(null);
  const moduleSearchBoxRef = useRef<HTMLDivElement>(null);
  const moduleSearchPanelRef = useRef<HTMLDivElement>(null);
  const normalizedModuleQuery = normalizeText(query);
  const filtered = records.filter((item) => {
    const haystack = `${item.title} ${item.subtitle} ${item.status ?? ""} ${item.amount ?? ""} ${item.stock ?? ""} ${item.price ?? ""} ${item.date ?? ""} ${item.client ?? ""} ${item.product ?? ""}`;
    const normalizedHaystack = normalizeText(haystack);
    const normalizedFilter = filter.toLocaleLowerCase("es").replace("pendientes", "pendiente").replace("recibidos", "recibido").replace("activos", "activo").replace("inactivos", "inactivo");
    const matchesFilter =
      Boolean(normalizedModuleQuery) ||
      filter === "Todos" ||
      filter === "Hoy" ||
      ["Ayer", "7 días", "30 días"].includes(filter) ||
      normalizedHaystack.includes(normalizedFilter);
    const matchesSearch = !normalizedModuleQuery || normalizedHaystack.includes(normalizedModuleQuery);
    return matchesFilter && matchesSearch;
  });

  const filters =
    module === "ventas" || module === "compras"
      ? ["Hoy", "Ayer", "7 días", "30 días"]
      : module === "pedidos"
        ? ["Todos", "Pendientes", "Recibidos"]
        : module === "inventario"
          ? ["Todos", "Res", "Cerdo", "Pollo", "Otros"]
          : ["Todos", "Activos", "Inactivos"];

  const total = records.reduce((sum, item) => sum + (item.amount ?? 0), 0);
  const active = records.filter((item) => !/inactivo|cancel/i.test(item.status ?? "")).length;
  const stock = records.reduce((sum, item) => sum + (item.stock ?? 0), 0);
  const inventoryLowStock = module === "inventario" ? records.filter((item) => item.stock !== undefined && item.stock <= 20).length : 0;
  const inventoryAvailable = module === "inventario" ? records.filter((item) => !/inactivo|agotado|cancel/i.test(item.status ?? "")).length : 0;
  const average = records.length ? total / records.length : 0;
  const editable = !["rendimiento", "informacion", "configuracion"].includes(module);
  const deletable = ["inventario", "clientes", "proveedores"].includes(module);
  const icon = sidebarItems.find((item) => item.module === module)?.icon ?? "chart-line";
  const lowStock = allRecords.inventario.filter((item) => item.stock !== undefined && item.stock <= 20);
  const moduleAlertCount = lowStock.length + (connectionStatus === "online" ? 0 : 1);
  const paidLoan = allRecords.prestamos.find((item) => /pagado|abono/i.test(`${item.status ?? ""} ${item.subtitle}`));
  const initials = username.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  const contextualCreationActions = [
    ...creationActions.filter((action) => action.module === module),
    ...creationActions.filter((action) => action.module !== module),
  ];
  const globalSales = allRecords.ventas.reduce((sum, item) => sum + (item.amount ?? 0), 0);
  const normalizeGlobalSearch = (value: string) =>
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLocaleLowerCase("es");
  const normalizedGlobalQuery = normalizeGlobalSearch(query);
  const globalModuleMatches = (Object.keys(moduleInfo) as ModuleKey[])
    .filter((key) =>
      normalizedGlobalQuery &&
      normalizeGlobalSearch(`${moduleInfo[key].title} ${moduleInfo[key].subtitle}`).includes(normalizedGlobalQuery),
    )
    .slice(0, 5);
  const globalRecordMatches = (Object.keys(allRecords) as ModuleKey[])
    .flatMap((key) => allRecords[key].map((item) => ({ ...item, module: key })))
    .filter((item) =>
      normalizedGlobalQuery &&
      normalizeGlobalSearch(`${item.title} ${item.subtitle} ${item.status ?? ""}`).includes(normalizedGlobalQuery),
    )
    .slice(0, 10);
  const analysisCards =
    module === "rendimiento"
      ? [
          { label: "Ventas acumuladas", value: money(globalSales), note: "Datos del sistema" },
          { label: "Operaciones", value: String(allRecords.ventas.length), note: "Ventas registradas" },
          { label: "Clientes", value: String(allRecords.clientes.length), note: "Base activa" },
          { label: "Inventario", value: String(allRecords.inventario.length), note: "Productos" },
        ]
      : module === "informacion" || module === "configuracion"
        ? [
            { label: "Productos", value: String(allRecords.inventario.length), note: "Inventario" },
            { label: "Clientes", value: String(allRecords.clientes.length), note: "Directorio" },
            { label: "Proveedores", value: String(allRecords.proveedores.length), note: "Directorio" },
            { label: "Pedidos", value: String(allRecords.pedidos.length), note: "Operaciones" },
          ]
        : [
            { label: "Registros", value: String(records.length), note: "Actualizados" },
            { label: module === "inventario" ? "Existencias" : "Total", value: module === "inventario" ? String(stock) : money(total), note: "Acumulado" },
            { label: "Activos", value: String(active), note: records.length ? `${Math.round((active / records.length) * 100)}%` : "0%" },
            { label: "Promedio", value: money(average), note: "Análisis" },
          ];

  useEffect(() => {
    try {
      const savedHistory = JSON.parse(localStorage.getItem("carnes-search-history") ?? "[]") as unknown;
      if (Array.isArray(savedHistory)) {
        setSearchHistory(savedHistory.filter((item): item is string => typeof item === "string").slice(0, 10));
      }
    } catch {
      localStorage.removeItem("carnes-search-history");
    }
  }, []);

  useEffect(() => {
    if (!globalSearchOpen) return;
    const closeSearchFromOutside = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (moduleSearchBoxRef.current?.contains(target) || moduleSearchPanelRef.current?.contains(target)) return;
      setGlobalSearchOpen(false);
    };
    document.addEventListener("pointerdown", closeSearchFromOutside);
    return () => document.removeEventListener("pointerdown", closeSearchFromOutside);
  }, [globalSearchOpen]);

  function saveGlobalSearch(term: string) {
    const cleanTerm = term.trim();
    if (!cleanTerm) return;
    setSearchHistory((current) => {
      const next = [cleanTerm, ...current.filter((item) => normalizeGlobalSearch(item) !== normalizeGlobalSearch(cleanTerm))].slice(0, 10);
      localStorage.setItem("carnes-search-history", JSON.stringify(next));
      return next;
    });
  }

  function openGeneralSearch() {
    setGlobalSearchOpen(true);
    setAlertsOpen(false);
    setNotificationsOpen(false);
    setProfileOpen(false);
    setMenuOpen(false);
  }

  function submitGeneralSearch() {
    openGeneralSearch();
    if (!query.trim()) return;
    saveGlobalSearch(query);
    const resultCount = globalModuleMatches.length + globalRecordMatches.length;
    setSearchMessage(
      resultCount
        ? `${resultCount} resultado${resultCount === 1 ? "" : "s"} encontrado${resultCount === 1 ? "" : "s"}.`
        : `No encontramos coincidencias para “${query.trim()}”.`,
    );
  }

  function openGeneralSearchResult(nextModule: ModuleKey, term = query) {
    saveGlobalSearch(term);
    setGlobalSearchOpen(false);
    setQuery("");
    setSearchMessage("");
    onModule(nextModule);
  }

  function closeToolbarPanels() {
    setMenuOpen(false);
    setAlertsOpen(false);
    setNotificationsOpen(false);
    setProfileOpen(false);
    setGlobalSearchOpen(false);
  }

  function startModuleVoiceSearch() {
    const voiceWindow = window as VoiceWindow;
    const Recognition = voiceWindow.SpeechRecognition ?? voiceWindow.webkitSpeechRecognition;
    if (!Recognition) {
      moduleSearchRef.current?.focus();
      return;
    }
    const recognition = new Recognition();
    recognition.lang = "es-MX";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim() ?? "";
      if (transcript) {
        setQuery(transcript);
        saveGlobalSearch(transcript);
        setSearchMessage(`Buscando “${transcript}”`);
        setGlobalSearchOpen(true);
      }
    };
    recognition.onerror = () => setVoiceListening(false);
    recognition.onend = () => setVoiceListening(false);
    try {
      setVoiceListening(true);
      recognition.start();
    } catch {
      setVoiceListening(false);
      moduleSearchRef.current?.focus();
    }
  }

  return (
    <section className={`screen module-screen dark-screen unified-module-screen ${module === "inventario" ? "inventory-module-screen" : ""}`}>
      <header className="home-toolbar module-global-toolbar">
        <button
          className="toolbar-menu-button"
          type="button"
          onClick={() => {
            const next = !menuOpen;
            closeToolbarPanels();
            setMenuOpen(next);
          }}
          aria-label="Abrir menú"
        >
          <img src="/icons/menu.svg" alt="" />
        </button>
        <div ref={moduleSearchBoxRef} className="toolbar-search-pill" role="search" onFocusCapture={openGeneralSearch}>
          <button className="toolbar-search-submit" type="button" onClick={submitGeneralSearch} aria-label="Buscar en todo el sistema">
            <img src="/icons/search.svg" alt="" />
          </button>
          <input
            ref={moduleSearchRef}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setSearchMessage("");
              setGlobalSearchOpen(true);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                submitGeneralSearch();
              }
              if (event.key === "Escape") {
                setQuery("");
                setSearchMessage("");
              }
            }}
            placeholder="Buscar"
            aria-label="Buscar en todo el sistema"
          />
          {query ? (
            <button className="toolbar-clear-search" type="button" onClick={() => { setQuery(""); setSearchMessage(""); setGlobalSearchOpen(true); moduleSearchRef.current?.focus(); }} aria-label="Limpiar búsqueda">×</button>
          ) : (
            <button className={voiceListening ? "toolbar-mic listening" : "toolbar-mic"} type="button" onClick={startModuleVoiceSearch} aria-label="Buscar con micrófono">
              <img src="/icons/mic.svg" alt="" />
            </button>
          )}
        </div>
        <div className="toolbar-actions">
          <button
            type="button"
            className={`alert-center-button ${moduleAlertCount ? "has-alerts" : ""}`}
            onClick={() => {
              const next = !alertsOpen;
              closeToolbarPanels();
              setAlertsOpen(next);
            }}
            aria-label={`Centro de notificaciones y alertas, ${moduleAlertCount} alertas`}
          >
            <img src="/icons/bell.svg" alt="" />
            {moduleAlertCount > 0 && <span>{moduleAlertCount}</span>}
          </button>
          <button
            type="button"
            className="create-center-button"
            onClick={() => {
              const next = !notificationsOpen;
              closeToolbarPanels();
              setNotificationsOpen(next);
            }}
            aria-label="Crear un nuevo registro"
          >
            <span aria-hidden="true">+</span>
          </button>
          <button
            type="button"
            className="profile-avatar"
            onClick={() => {
              const next = !profileOpen;
              closeToolbarPanels();
              setProfileOpen(next);
            }}
            aria-label="Abrir perfil"
          >
            {initials}<span className="profile-online-dot" />
          </button>
        </div>
      </header>

      {globalSearchOpen && (
        <div ref={moduleSearchPanelRef} className="inline-search-dropdown module-global-search-dropdown">
          {searchMessage && <div className={`voice-search-status ${voiceListening ? "listening" : ""}`}><span />{searchMessage}</div>}
          {!normalizedGlobalQuery ? (
            <>
              <header className="search-history-heading">
                <div><img src="/icons/history.svg" alt="" /><strong>Búsquedas recientes</strong></div>
                {searchHistory.length > 0 && (
                  <button type="button" onClick={() => { setSearchHistory([]); localStorage.removeItem("carnes-search-history"); }}>Borrar</button>
                )}
              </header>
              <div className="search-history-list">
                {searchHistory.map((term) => (
                  <button type="button" key={term} onClick={() => { setQuery(term); setSearchMessage(""); setGlobalSearchOpen(true); moduleSearchRef.current?.focus(); }}>
                    <img src="/icons/history.svg" alt="" />
                    <span>{term}</span>
                    <b>↗</b>
                  </button>
                ))}
                {searchHistory.length === 0 && <p>Aquí aparecerán tus búsquedas recientes.</p>}
              </div>
            </>
          ) : (
            <div className="inline-search-results">
              {globalModuleMatches.length > 0 && (
                <div className="search-result-group">
                  <small>Módulos</small>
                  {globalModuleMatches.map((nextModule) => (
                    <button type="button" key={nextModule} onClick={() => openGeneralSearchResult(nextModule)}>
                      <span className="search-result-icon"><img src="/icons/package.svg" alt="" /></span>
                      <span><strong>{moduleInfo[nextModule].title}</strong><small>{moduleInfo[nextModule].subtitle}</small></span>
                      <b>›</b>
                    </button>
                  ))}
                </div>
              )}
              {globalRecordMatches.length > 0 && (
                <div className="search-result-group">
                  <small>Resultados de todo el sistema</small>
                  {globalRecordMatches.map((item) => (
                    <button type="button" key={`${item.module}-${item.id}`} onClick={() => openGeneralSearchResult(item.module)}>
                      <span className="search-result-icon"><img src="/icons/search.svg" alt="" /></span>
                      <span><strong>{item.title}</strong><small>{moduleInfo[item.module].title} · {item.subtitle}</small></span>
                      <b>›</b>
                    </button>
                  ))}
                </div>
              )}
              {globalModuleMatches.length === 0 && globalRecordMatches.length === 0 && (
                <div className="inline-search-empty"><strong>Sin resultados</strong><span>No encontramos coincidencias para “{query}”.</span></div>
              )}
            </div>
          )}
        </div>
      )}

      {menuOpen && (
        <SidebarMenu
          username={username}
          onClose={() => setMenuOpen(false)}
          onModule={(nextModule) => {
            closeToolbarPanels();
            onModule(nextModule);
          }}
          onLogout={onLogout}
        />
      )}
      {alertsOpen && (
        <div className="home-popover alert-center-panel module-toolbar-panel">
          <header><div><strong>Notificaciones y alertas</strong><small>Actividad reciente del sistema</small></div><img src="/icons/bell.svg" alt="" /></header>
          <button type="button" className="notification-event" onClick={() => { closeToolbarPanels(); onModule("inventario"); }}>
            <span><img src="/icons/package.svg" alt="" /></span>
            <span><strong>Inventario actualizado</strong><small>{allRecords.inventario.length} productos sincronizados.</small></span>
            <b>›</b>
          </button>
          {paidLoan && (
            <button type="button" className="notification-event payment-event" onClick={() => { closeToolbarPanels(); onModule("prestamos"); }}>
              <span><img src="/icons/hand-coins.svg" alt="" /></span>
              <span><strong>Abono recibido</strong><small>{paidLoan.title} · {paidLoan.subtitle}</small></span>
              <b>›</b>
            </button>
          )}
          {lowStock.map((item) => (
            <button type="button" className="system-alert stock-alert" key={item.id} onClick={() => { closeToolbarPanels(); onModule("inventario"); }}>
              <span><img src="/icons/package.svg" alt="" /></span>
              <span><strong>Stock bajo: {item.title}</strong><small>Quedan {item.stock} unidades.</small></span>
              <b>›</b>
            </button>
          ))}
          {connectionStatus !== "online" && (
            <div className="system-alert connection-alert">
              <span><img src="/icons/wifi-off.svg" alt="" /></span>
              <span><strong>Sistema sin sincronización</strong><small>Comprueba la conexión con la API.</small></span>
              <b>!</b>
            </div>
          )}
          {connectionStatus === "online" && <div className="alerts-ok"><img src="/icons/circle-check.svg" alt="" /><span><strong>Sistema sincronizado</strong><small>La información está actualizada.</small></span></div>}
        </div>
      )}
      {notificationsOpen && (
        <div className="create-sheet-backdrop" onPointerDown={(event) => { if (event.target === event.currentTarget) setNotificationsOpen(false); }}>
          <section className="create-menu-panel create-bottom-sheet" role="dialog" aria-modal="true" aria-label="Crear un nuevo registro">
            <span className="bottom-sheet-handle" aria-hidden="true" />
            <header><div><strong>Crear</strong><small>{moduleInfo[module].title}</small></div><span>+</span></header>
            <div className="create-menu-list">
              {contextualCreationActions.map((action) => (
                <button
                  type="button"
                  key={action.module}
                  className={action.module === module ? "recommended" : ""}
                  onClick={() => {
                    closeToolbarPanels();
                    onQuickAdd(action.module);
                  }}
                >
                  <span><img src={`/icons/${action.icon}.svg`} alt="" /></span>
                  <span><strong>{action.label}</strong><small>{action.module === module ? "Opción recomendada para este módulo" : action.detail}</small></span>
                  <b>›</b>
                </button>
              ))}
            </div>
          </section>
        </div>
      )}
      {profileOpen && (
        <div className="home-popover module-toolbar-profile module-toolbar-panel">
          <span className="profile-avatar large">{initials}</span>
          <strong>{username}</strong>
          <small>Usuario autorizado · Carnes Luévanos</small>
          <button type="button" onClick={() => { closeToolbarPanels(); onModule("configuracion"); }}>Perfil y seguridad</button>
          <button className="logout" type="button" onClick={onLogout}>Cerrar sesión</button>
        </div>
      )}

      <header className="module-toolbar">
        <div className="module-toolbar-title">
          {onBack && <button className="module-back" type="button" onClick={onBack}>‹</button>}
          <span><img src={`/icons/${icon}.svg`} alt="" /></span>
          <div><h1>{moduleInfo[module].title}</h1><small>{moduleInfo[module].subtitle}</small></div>
        </div>
        <div className="module-header-actions">
          {module === "inventario" ? (
            <button className="inventory-summary-trigger" type="button" onClick={() => setInventoryMenuOpen((open) => !open)} aria-label="Abrir resumen de inventario">
              <img src="/icons/filter.svg" alt="" />
            </button>
          ) : (
            <span className={`module-sync-state ${connectionStatus}`}><i />{connectionStatus === "online" ? "En línea" : "Sin conexión"}</span>
          )}
          <button className="module-header-create" type="button" onClick={onAdd} aria-label={`Crear registro en ${moduleInfo[module].title}`}>
            <span aria-hidden="true">+</span>
          </button>
        </div>
      </header>

      {module === "inventario" && inventoryMenuOpen && (
        <div className="inventory-summary-card">
          <article><small>Registros</small><strong>{records.length}</strong><span>Productos cargados</span></article>
          <article><small>Existencias</small><strong>{stock}</strong><span>kg/unidades</span></article>
          <article><small>Disponibles</small><strong>{inventoryAvailable}</strong><span>Activos</span></article>
          <article><small>Stock bajo</small><strong>{inventoryLowStock}</strong><span>Revisar</span></article>
        </div>
      )}

      <label className="module-inline-search">
        <img src="/icons/search.svg" alt="" />
        <input
          ref={moduleSearchRef}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Buscar en ${moduleInfo[module].title.toLocaleLowerCase("es")}`}
          aria-label={`Buscar en ${moduleInfo[module].title}`}
        />
        {query && <button type="button" onClick={() => { setQuery(""); moduleSearchRef.current?.focus(); }} aria-label="Limpiar búsqueda">×</button>}
      </label>

      <div className="module-analysis-grid">
        {analysisCards.map((card) => (
          <article key={card.label}>
            <small>{card.label}</small>
            <strong>{card.value}</strong>
            <em>{card.note}</em>
          </article>
        ))}
      </div>

      <div className="filter-row">
        {filters.map((item) => (
          <button className={filter === item ? "active" : ""} key={item} onClick={() => setFilter(item)}>{item}</button>
        ))}
      </div>
      <div className="module-section-heading"><div><strong>Actividad reciente</strong><small>{filtered.length} resultados</small></div></div>
      <div className="record-list">
        {filtered.map((item) => module === "inventario" ? (
          <article className="inventory-product-card" key={item.id} role="button" tabIndex={0} onClick={() => setSelectedInventoryItem(item)} onKeyDown={(event) => { if (event.key === "Enter") setSelectedInventoryItem(item); }}>
            <span className={saleImageSrc(item.image) ? "inventory-product-image with-image" : "inventory-product-image"}>
              {saleImageSrc(item.image) ? <img src={saleImageSrc(item.image)} alt={item.title} onError={(event) => { event.currentTarget.style.display = "none"; }} /> : <img src="/icons/package.svg" alt="" />}
            </span>
            <div className="inventory-product-copy">
              <strong>{item.title}</strong>
              <small>{item.subtitle || `SKU: INV-${String(item.id).padStart(3, "0")}`}</small>
              {item.price != null && <b>{money(item.price)} / kg</b>}
            </div>
            <div className="inventory-product-meta">
              {item.status && <Status value={item.status} />}
              {item.stock != null && <small>{item.stock} kg</small>}
              {deletable && <button className="delete" onClick={(event) => { event.stopPropagation(); onDelete(item.id); }} aria-label={`Eliminar ${item.title}`}>×</button>}
            </div>
          </article>
        ) : (
          <article className="record-card" key={item.id}>
            <span className="avatar"><img src={`/icons/${icon}.svg`} alt="" /></span>
            <div className="record-copy">
              <strong>{item.title}</strong>
              <small>{item.subtitle}</small>
              {item.price != null && <b>{money(item.price)} / kg</b>}
            </div>
            <div className="record-meta">
              {item.amount != null && <strong>{money(item.amount)}</strong>}
              {item.stock != null && <small>{item.stock} kg</small>}
              {item.status && <Status value={item.status} />}
              {deletable && <button className="delete" onClick={() => onDelete(item.id)} aria-label={`Eliminar ${item.title}`}>×</button>}
            </div>
          </article>
        ))}
        {!filtered.length && <div className="empty">No hay registros para este filtro.</div>}
      </div>
      {selectedInventoryItem && (
        <InventoryDetailSheet
          item={selectedInventoryItem}
          onClose={() => setSelectedInventoryItem(null)}
          onEdit={() => {
            setSelectedInventoryItem(null);
            onAdd();
          }}
          onDelete={() => {
            onDelete(selectedInventoryItem.id);
            setSelectedInventoryItem(null);
          }}
        />
      )}
    </section>
  );
}

type SalesPeriod = "Hoy" | "Ayer" | "7 días" | "30 días";

function InventoryDetailSheet({
  item,
  onClose,
  onEdit,
  onDelete,
}: {
  item: RecordItem;
  onClose: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const image = saleImageSrc(item.image);
  const sku = item.subtitle || `SKU: INV-${String(item.id).padStart(3, "0")}`;
  const category = inferInventoryCategory(`${item.title} ${item.subtitle}`);
  const minStock = Math.max(5, Math.min(20, Math.round((item.stock ?? 20) * 0.15)));

  return (
    <div className="inventory-detail-backdrop" onPointerDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="inventory-detail-card" role="dialog" aria-modal="true" aria-label={`Detalle de ${item.title}`}>
        <header>
          <button type="button" className="inventory-detail-back" onClick={onClose} aria-label="Regresar">‹</button>
          <h2>Detalle del producto</h2>
          <button type="button" className="inventory-detail-edit-icon" onClick={onEdit} aria-label="Editar producto"><span>✎</span></button>
        </header>

        <div className="inventory-detail-hero">
          <span className={image ? "inventory-detail-image with-image" : "inventory-detail-image"}>
            {image ? <img src={image} alt={item.title} onError={(event) => { event.currentTarget.style.display = "none"; }} /> : <img src="/icons/package.svg" alt="" />}
          </span>
          <div>
            <h3>{item.title}</h3>
            {item.status && <Status value={item.status} />}
            <strong>{money(item.price ?? 0)} <small>/ kg</small></strong>
          </div>
        </div>

        <div className="inventory-detail-specs">
          <DetailRow label="SKU" value={sku} />
          <DetailRow label="Categoría" value={category} />
          <DetailRow label="Costo" value={`${money(item.amount ?? 0)} / kg`} />
          <DetailRow label="Stock actual" value={`${item.stock ?? 0} kg`} />
          <DetailRow label="Stock mínimo" value={`${minStock} kg`} />
          <DetailRow label="Proveedor" value="Carnes Luévanos" />
        </div>

        <div className="inventory-detail-description">
          <small>Descripción</small>
          <p>{category === "Res" ? "Corte seleccionado de res listo para venta." : `Producto registrado en inventario: ${item.title}.`}</p>
        </div>

        <footer>
          <button type="button" className="edit" onClick={onEdit}><span>✎</span>Editar</button>
          <button type="button" className="delete" onClick={onDelete}><span>⌫</span>Eliminar</button>
        </footer>
      </section>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return <article><span>{label}</span><strong>{value}</strong></article>;
}

function inferInventoryCategory(value: string) {
  const text = normalizeText(value);
  if (/res|bistec|canal|diezmillo|recorte|novillo/.test(text)) return "Res";
  if (/cerdo|puerco|chuleta/.test(text)) return "Cerdo";
  if (/pollo|pechuga/.test(text)) return "Pollo";
  return "Otros";
}

function SalesModuleView({
  records,
  onBack,
  onAdd,
  connectionStatus,
}: {
  records: RecordItem[];
  onBack?: () => void;
  onAdd: () => void;
  connectionStatus: "demo" | "connecting" | "online" | "offline";
}) {
  const [period, setPeriod] = useState<SalesPeriod>("Hoy");
  const [salesQuery, setSalesQuery] = useState("");
  const normalizedQuery = normalizeText(salesQuery);
  const periodSales = records.filter((item) => saleMatchesPeriod(item, period));
  const visibleSales = (normalizedQuery ? records : periodSales).filter((item) => {
    if (!normalizedQuery) return true;
    return normalizeText(`${item.title} ${item.client ?? ""} ${item.subtitle} ${item.product ?? ""} ${item.status ?? ""}`).includes(normalizedQuery);
  });
  const total = visibleSales.reduce((sum, item) => sum + (item.amount ?? 0), 0);
  const previousTotal = records
    .filter((item) => saleMatchesPreviousPeriod(item, period))
    .reduce((sum, item) => sum + (item.amount ?? 0), 0);
  const trend = previousTotal > 0 ? ((total - previousTotal) / previousTotal) * 100 : total > 0 ? 100 : 0;
  const barValues = buildSalesBars(visibleSales);
  const maxBar = Math.max(...barValues, 1);
  const periodLabel = normalizedQuery ? "todas las ventas" : period.toLocaleLowerCase("es");

  return (
    <section className="screen sales-module-screen">
      <header className="sales-module-header">
        <div>
          {onBack && <button className="sales-back-button" type="button" onClick={onBack} aria-label="Regresar">‹</button>}
          <span className="sales-title-icon" aria-hidden="true"><img src="/icons/shopping-cart.svg" alt="" /></span>
          <div className="sales-title-copy">
            <h1>Ventas</h1>
            <small>Gestiona tus ventas</small>
          </div>
        </div>
        <span className={`sales-online-pill ${connectionStatus}`}>
          <i />
          {connectionStatus === "online" ? "En línea" : connectionStatus === "connecting" ? "Conectando" : "Sin conexión"}
        </span>
      </header>

      <label className="sales-search">
        <img src="/icons/search.svg" alt="" />
        <input
          value={salesQuery}
          onChange={(event) => setSalesQuery(event.target.value)}
          placeholder="Buscar ventas, cliente o producto"
          aria-label="Buscar ventas"
        />
        {salesQuery && <button type="button" onClick={() => setSalesQuery("")} aria-label="Limpiar búsqueda">×</button>}
      </label>

      <div className="sales-period-tabs" role="tablist" aria-label="Filtrar ventas por periodo">
        {(["Hoy", "Ayer", "7 días", "30 días"] as SalesPeriod[]).map((item) => (
          <button type="button" key={item} className={period === item ? "active" : ""} onClick={() => setPeriod(item)}>
            {item}
          </button>
        ))}
      </div>

      <article className="sales-summary-card">
        <div className="sales-summary-copy">
          <small>Ventas {periodLabel}</small>
          <strong>{money(total)}</strong>
          <span className={trend >= 0 ? "positive" : "negative"}>{trend >= 0 ? "↑" : "↓"} {Math.abs(trend).toFixed(1)}% vs periodo anterior</span>
        </div>
        <div className="sales-bars" aria-label="Gráfica de ventas">
          {barValues.map((value, index) => (
            <i key={`${index}-${value}`} style={{ height: `${Math.max(8, (value / maxBar) * 64)}px`, opacity: value ? 1 : 0.28 }} />
          ))}
        </div>
      </article>

      <div className="sales-section-label">
        <strong>Últimas ventas</strong>
        <small>{visibleSales.length} resultado{visibleSales.length === 1 ? "" : "s"}</small>
      </div>

      <div className="sales-list">
        {visibleSales.map((item) => {
          const image = saleImageSrc(item.image);
          return (
            <article className="sales-row" key={item.id}>
              <span className={image ? "sales-thumb with-image" : "sales-thumb"}>
                {image ? <img src={image} alt={item.product ?? item.title} onError={(event) => { event.currentTarget.style.display = "none"; }} /> : <img src="/icons/receipt-text.svg" alt="" />}
              </span>
              <div className="sales-row-main">
                <strong>{item.title}</strong>
                <small>{item.client ?? item.subtitle}</small>
                {item.product && <em>{item.product}</em>}
              </div>
              <div className="sales-row-meta">
                <time>{saleTimeLabel(item)}</time>
                <b>{money(item.amount ?? 0)}</b>
                <span className={saleStatusClass(item.status)}>{item.status ?? "Pagado"}</span>
              </div>
            </article>
          );
        })}
        {!visibleSales.length && (
          <div className="sales-empty">
            <img src="/icons/receipt-text.svg" alt="" />
            <strong>Sin ventas</strong>
            <span>{salesQuery ? "No encontramos ventas con esa búsqueda." : "No hay ventas registradas para este periodo."}</span>
          </div>
        )}
      </div>
    </section>
  );
}

function normalizeText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLocaleLowerCase("es");
}

function sameCalendarDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function saleMatchesPeriod(item: RecordItem, period: SalesPeriod) {
  const date = parseSaleDate(item.date);
  if (!date) return period !== "Hoy" && period !== "Ayer";
  const now = new Date();
  const start = new Date(now);
  if (period === "Hoy") return sameCalendarDay(date, now);
  if (period === "Ayer") {
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    return sameCalendarDay(date, yesterday);
  }
  start.setHours(0, 0, 0, 0);
  start.setDate(now.getDate() - (period === "7 días" ? 6 : 29));
  return date >= start && date <= now;
}

function saleMatchesPreviousPeriod(item: RecordItem, period: SalesPeriod) {
  const date = parseSaleDate(item.date);
  if (!date) return false;
  const now = new Date();
  const start = new Date(now);
  const end = new Date(now);
  start.setHours(0, 0, 0, 0);
  end.setHours(23, 59, 59, 999);
  if (period === "Hoy") {
    start.setDate(now.getDate() - 1);
    end.setDate(now.getDate() - 1);
  } else if (period === "Ayer") {
    start.setDate(now.getDate() - 2);
    end.setDate(now.getDate() - 2);
  } else {
    const span = period === "7 días" ? 7 : period === "30 días" ? 30 : 30;
    end.setDate(now.getDate() - span);
    start.setDate(now.getDate() - span * 2 + 1);
  }
  return date >= start && date <= end;
}

function buildSalesBars(items: RecordItem[]) {
  const sales = items.slice(-14);
  if (!sales.length) return Array.from({ length: 14 }, () => 0);
  return Array.from({ length: 14 }, (_, index) => sales[index]?.amount ?? 0);
}

function saleImageSrc(image?: string) {
  const clean = (image ?? "").trim().replace(/\\/g, "/");
  if (!clean) return "";
  if (/^https?:\/\//i.test(clean) || clean.startsWith("/")) return clean;
  const staticIndex = clean.toLocaleLowerCase("es").indexOf("/static/");
  if (staticIndex >= 0) return clean.slice(staticIndex);
  const uploadsIndex = clean.toLocaleLowerCase("es").indexOf("/uploads/");
  if (uploadsIndex >= 0) return clean.slice(uploadsIndex);
  return "";
}

function saleTimeLabel(item: RecordItem) {
  if (item.time) return item.time.slice(0, 5);
  const date = parseSaleDate(item.date);
  if (!date) return "Ahora";
  return date.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
}

function saleStatusClass(status?: string) {
  const value = status ?? "";
  if (/pendiente|credito|crédito/i.test(value)) return "sales-status pending";
  if (/cancel|rechaz/i.test(value)) return "sales-status negative";
  return "sales-status paid";
}

function MiniBars() {
  return <div className="mini-bars">{[32, 46, 25, 62, 48, 79, 55, 88].map((n, i) => <i key={i} style={{ height: n }} />)}</div>;
}

function Status({ value }: { value: string }) {
  const negative = /inactivo|cancel/i.test(value);
  const pending = /pendiente/i.test(value);
  return <span className={`status ${negative ? "negative" : pending ? "pending" : ""}`}>{value}</span>;
}

function Performance({ onBack }: { onBack?: () => void }) {
  return (
    <section className="screen light-screen">
      <header className="simple-header"><div className="header-title">{onBack && <button className="back" onClick={onBack}>‹</button>}<h1>Rendimiento</h1></div></header>
      <p className="section-label">KPIs principales</p>
      <div className="kpi-grid">
        {[["Ventas totales", "$624,850", "+14.2%"], ["Margen bruto", "32.8%", "+4.1%"], ["Clientes nuevos", "128", "+18.7%"], ["Ticket promedio", "$1,250", "+15.3%"]].map(([a, b, c]) => <article key={a}><small>{a}</small><strong>{b}</strong><em>{c}</em></article>)}
      </div>
      <article className="performance-chart"><div className="section-heading"><h3>Ventas vs. tiempo</h3><span>Este mes</span></div><LineChart /></article>
    </section>
  );
}

function Information({ onBack }: { onBack?: () => void }) {
  const rows = [["Empresa", "Carnes Luévanos"], ["Dirección", "Av. Principal #123"], ["Teléfono", "55 1234 5678"], ["Correo electrónico", "info@carnesluevanos.com"], ["RFC", "CLU760101AAA"], ["Moneda", "MXN · peso mexicano"], ["Configuración de impresión", "Ver configuración"]];
  return <section className="screen light-screen"><header className="simple-header"><div className="header-title">{onBack && <button className="back" onClick={onBack}>‹</button>}<h1>Información</h1></div></header><div className="settings-list">{rows.map(([title, value]) => <article key={title}><span className="settings-icon">ⓘ</span><div><strong>{title}</strong><small>{value}</small></div><b>›</b></article>)}</div></section>;
}

function Settings({ onBack }: { onBack?: () => void }) {
  const rows = ["Perfil de empresa", "Usuarios y permisos", "Roles", "Métodos de pago", "Impuestos", "Notificaciones", "Respaldo y seguridad", "Sincronización en la nube", "Acerca de la app"];
  const [selected, setSelected] = useState<string | null>(null);
  return <section className="screen light-screen"><header className="simple-header"><div className="header-title">{onBack && <button className="back" onClick={onBack}>‹</button>}<h1>Configuración</h1></div></header><div className="settings-list">{rows.map((title) => <button key={title} onClick={() => setSelected(title)}><span className="settings-icon">⚙</span><strong>{title}</strong><b>›</b></button>)}</div>{selected && <div className="inline-panel"><h3>{selected}</h3><label className="toggle-row"><span>Habilitado</span><input type="checkbox" defaultChecked /></label><button className="primary" onClick={() => setSelected(null)}>Guardar</button></div>}</section>;
}

function RecordModal({
  module,
  onClose,
  onSave,
}: {
  module: ModuleKey;
  onClose: () => void;
  onSave: (item: RecordItem) => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [amount, setAmount] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaveError("");
    try {
      await onSave({
        id: Date.now(),
        title,
        subtitle,
        amount: amount ? Number(amount) : undefined,
        stock: module === "inventario" && amount ? Number(amount) : undefined,
        price: module === "inventario" ? 0 : undefined,
        status: module === "pedidos" ? "Pendiente" : "Activo",
      });
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "No se pudo sincronizar el registro.");
    } finally {
      setSaving(false);
    }
  }
  const titleLabel = module === "ventas" ? "Cliente" : module === "compras" || module === "pedidos" ? "Proveedor" : module === "inventario" ? "Producto" : "Nombre o concepto";
  const detailLabel = module === "ventas" || module === "compras" ? "Producto o código" : module === "proveedores" ? "RFC o identificación" : module === "nominas" ? "Periodo" : "Detalle";
  const amountLabel = module === "inventario" ? "Stock inicial" : module === "ventas" || module === "compras" ? "Cantidad" : "Monto";
  const modalIcon = creationActions.find((action) => action.module === module)?.icon ?? "package";
  return (
    <div className="modal-backdrop" onPointerDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="modal-card bottom-sheet-card" role="dialog" aria-modal="true" aria-label={`Crear en ${moduleInfo[module].title}`}>
        <span className="bottom-sheet-handle" aria-hidden="true" />
        <header>
          <div className="bottom-sheet-heading">
            <span><img src={`/icons/${modalIcon}.svg`} alt="" /></span>
            <div><small>Crear nuevo registro</small><h2>{moduleInfo[module].title}</h2></div>
          </div>
          <button type="button" onClick={onClose} aria-label="Cerrar formulario">×</button>
        </header>
        <form onSubmit={submit}>
          <label>{titleLabel}<input value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus /></label>
          <label>{detailLabel}<input value={subtitle} onChange={(e) => setSubtitle(e.target.value)} placeholder="Información del registro" /></label>
          <label>{amountLabel}<input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" inputMode="decimal" /></label>
          {saveError && <p className="modal-save-error">{saveError}</p>}
          <div className="bottom-sheet-actions">
            <button className="ghost" type="button" onClick={onClose} disabled={saving}>Cancelar</button>
            <button className="primary" disabled={saving}>{saving ? "Sincronizando…" : "Guardar en app y sistema"}</button>
          </div>
        </form>
      </section>
    </div>
  );
}

function JeloxChat({
  callApi,
  username,
  onClose,
  fabVisible,
  onFabVisibilityChange,
}: {
  callApi: (path: string, options?: RequestInit) => Promise<unknown>;
  username: string;
  onClose: () => void;
  fabVisible: boolean;
  onFabVisibilityChange: (visible: boolean) => void;
}) {
  const [messages, setMessages] = useState([{ user: false, text: "Hola, soy JELOX IA. Puedo ayudarte con ventas, inventario, clientes y alertas." }]);
  const [text, setText] = useState("");
  const [chatSearch, setChatSearch] = useState("");
  const [chatTab, setChatTab] = useState<"chat" | "acciones" | "nota">("chat");
  const [note, setNote] = useState("");
  const [noteSaved, setNoteSaved] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setNote(localStorage.getItem("jelox-quick-note") ?? "");
    setVoiceEnabled(localStorage.getItem("jelox-voice-enabled") === "true");
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
    }
  }, []);
  function getHumanVoice() {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return undefined;
    const voices = window.speechSynthesis.getVoices();
    if (!voices.length) return undefined;
    const preferredNames = /paulina|m[oó]nica|monica|jorge|diego|samantha|google espa/i;
    return (
      voices.find((voice) => preferredNames.test(voice.name) && /^es(-|_)?/i.test(voice.lang)) ||
      voices.find((voice) => /^es(-|_)?mx/i.test(voice.lang)) ||
      voices.find((voice) => /^es(-|_)?us/i.test(voice.lang)) ||
      voices.find((voice) => /^es(-|_)?es/i.test(voice.lang)) ||
      voices.find((voice) => /^es/i.test(voice.lang))
    );
  }
  function speak(textToSpeak: string) {
    try {
      if (!voiceEnabled || typeof window === "undefined" || !("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      const voice = getHumanVoice();
      if (voice) utterance.voice = voice;
      utterance.lang = "es-MX";
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.95;
      window.speechSynthesis.speak(utterance);
    } catch {
      // La voz es opcional; no debe bloquear la respuesta escrita.
    }
  }
  function toggleVoice() {
    setVoiceEnabled((current) => {
      const next = !current;
      localStorage.setItem("jelox-voice-enabled", String(next));
      try {
        if (!next && typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
        if (next && typeof window !== "undefined" && "speechSynthesis" in window) {
          setTimeout(() => {
            const cleanName = username?.trim() || "usuario";
            const utterance = new SpeechSynthesisUtterance(`Hola, ${cleanName}. ¿En qué te puedo ayudar?`);
            const voice = getHumanVoice();
            if (voice) utterance.voice = voice;
            utterance.lang = "es-MX";
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 0.95;
            window.speechSynthesis.speak(utterance);
          }, 0);
        }
      } catch {
        // La voz es opcional; JELOX debe seguir contestando por texto.
      }
      return next;
    });
  }
  async function send(value = text) {
    const question = value.trim();
    if (!question || busy) return;
    setText("");
    setChatSearch("");
    setMessages((list) => [...list, { user: true, text: question }]);
    setBusy(true);
    try {
      const result = (await Promise.race([
        callApi("/api/mobile/jelox/chat", { method: "POST", body: JSON.stringify({ message: question }) }),
        new Promise((_, reject) => window.setTimeout(() => reject(new Error("JELOX timeout")), 6500)),
      ])) as { answer?: string };
      const answer = result.answer ?? "Consulta procesada.";
      setMessages((list) => [...list, { user: false, text: answer }]);
      speak(answer);
    } catch {
      const answer = /stock|inventario/i.test(question)
        ? "Revisa primero los productos con menos de 5 kg y genera un pedido al proveedor."
        : /venta/i.test(question)
          ? "Las ventas muestran una tendencia positiva. Puedes abrir Rendimiento para ver los KPIs."
          : "Puedo analizar ventas, inventario, compras, pedidos y clientes cuando conectes la API.";
      setMessages((list) => [...list, { user: false, text: answer }]);
      speak(answer);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="chat-panel">
      <header className="jelox-chat-header">
        <div><img src="/jelox-welcome-hd.png" alt="" /><span><strong>JELOX</strong><small><i /> Asistente activo</small></span></div>
        <div className="jelox-chat-window-actions">
          <button className={voiceEnabled ? "active" : ""} type="button" onClick={toggleVoice} aria-label={voiceEnabled ? "Desactivar voz de JELOX" : "Activar voz de JELOX"}>Voz</button>
          <button type="button" onClick={onClose} aria-label="Cerrar JELOX">×</button>
        </div>
      </header>
      <div className="jelox-floating-controls">
        <button type="button" className={fabVisible ? "active" : ""} onClick={() => onFabVisibilityChange(true)}>Mostrar flotante</button>
        <button type="button" className={!fabVisible ? "active danger" : "danger"} onClick={() => onFabVisibilityChange(false)}>Quitar flotante</button>
      </div>
      <div className="jelox-chat-search"><img src="/icons/search.svg" alt="" /><input value={chatSearch} onChange={(event) => setChatSearch(event.target.value)} placeholder="Buscar en el chat" /></div>
      <nav className="jelox-chat-tabs">
        <button className={chatTab === "chat" ? "active" : ""} onClick={() => setChatTab("chat")}>Chat</button>
        <button className={chatTab === "acciones" ? "active" : ""} onClick={() => setChatTab("acciones")}>Acciones</button>
        <button className={chatTab === "nota" ? "active" : ""} onClick={() => setChatTab("nota")}>Nota</button>
      </nav>
      <div className="jelox-ready"><span>!</span><div><strong>JELOX está listo</strong><small>Pregunta, consulta el negocio o crea una nota.</small></div></div>
      {chatTab === "chat" && (
        <>
          <div className="messages">
            {messages.filter((message) => message.text.toLocaleLowerCase("es").includes(chatSearch.toLocaleLowerCase("es"))).map((msg, index) => (
              <div className={msg.user ? "message-row user" : "message-row"} key={index}>
                {!msg.user && <img src="/jelox-welcome-hd.png" alt="" />}
                <p>{msg.text}</p>
              </div>
            ))}
            {busy && (
              <div className="message-row">
                <img src="/jelox-welcome-hd.png" alt="" />
                <p className="thinking">JELOX está pensando…</p>
              </div>
            )}
          </div>
          <div className="suggestions">{["Resumen de hoy", "Stock bajo", "Buscar cliente"].map((x) => <button key={x} type="button" disabled={busy} onClick={() => send(x)}>{x}</button>)}</div>
          <form onSubmit={(e) => { e.preventDefault(); send(); }}><input value={text} disabled={busy} onChange={(e) => setText(e.target.value)} placeholder="Escribe a JELOX…" /><button type="submit" disabled={busy} aria-label="Enviar">➤</button></form>
        </>
      )}
      {chatTab === "acciones" && <div className="jelox-action-list">{["Analizar ventas", "Revisar stock bajo", "Consultar pedidos", "Buscar clientes"].map((action) => <button key={action} type="button" disabled={busy} onClick={() => { setChatTab("chat"); send(action); }}>{action}<span>›</span></button>)}<button type="button" onClick={() => onFabVisibilityChange(!fabVisible)}>{fabVisible ? "Quitar botón flotante" : "Mostrar botón flotante"}<span>›</span></button></div>}
      {chatTab === "nota" && <div className="jelox-note"><textarea value={note} onChange={(event) => { setNote(event.target.value); setNoteSaved(false); }} placeholder="Escribe una nota rápida…" /><button onClick={() => { localStorage.setItem("jelox-quick-note", note); setNoteSaved(true); }}>{noteSaved ? "Nota guardada ✓" : "Guardar nota"}</button></div>}
    </div>
  );
}

function MovableJeloxButton({ onOpen }: { onOpen: () => void }) {
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const drag = useRef({ pointerId: -1, startX: 0, startY: 0, originX: 0, originY: 0, moved: false });

  useEffect(() => {
    const saved = localStorage.getItem("jelox-fab-position");
    if (!saved) return;
    try {
      const value = JSON.parse(saved) as { x: number; y: number };
      setPosition({
        x: Math.max(10, Math.min(value.x, window.innerWidth - 74)),
        y: Math.max(12, Math.min(value.y, window.innerHeight - 86)),
      });
    } catch {
      localStorage.removeItem("jelox-fab-position");
    }
  }, []);

  const beginDrag = (event: ReactPointerEvent<HTMLButtonElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    event.currentTarget.setPointerCapture(event.pointerId);
    drag.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      originX: bounds.left,
      originY: bounds.top,
      moved: false,
    };
  };

  const moveDrag = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (drag.current.pointerId !== event.pointerId) return;
    const deltaX = event.clientX - drag.current.startX;
    const deltaY = event.clientY - drag.current.startY;
    if (Math.hypot(deltaX, deltaY) > 5) drag.current.moved = true;
    if (!drag.current.moved) return;
    setPosition({
      x: Math.max(10, Math.min(drag.current.originX + deltaX, window.innerWidth - 74)),
      y: Math.max(12, Math.min(drag.current.originY + deltaY, window.innerHeight - 86)),
    });
  };

  const endDrag = (event: ReactPointerEvent<HTMLButtonElement>) => {
    if (drag.current.pointerId !== event.pointerId) return;
    if (drag.current.moved) {
      setPosition((current) => {
        if (current) localStorage.setItem("jelox-fab-position", JSON.stringify(current));
        return current;
      });
    } else {
      onOpen();
    }
    drag.current.pointerId = -1;
  };

  return (
    <button
      className="jelox-fab"
      style={position ? { left: position.x, top: position.y, right: "auto", bottom: "auto" } : undefined}
      type="button"
      onPointerDown={beginDrag}
      onPointerMove={moveDrag}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      aria-label="Abrir o mover JELOX Studio IA"
    >
      <span><img src="/jelox-welcome-hd.png" alt="" draggable={false} /></span>
    </button>
  );
}

function BottomNav({ tab, isAdmin, onChange }: { tab: Tab; isAdmin: boolean; onChange: (tab: Tab) => void }) {
  const tabs: Array<[Tab, string, string]> = [
    ["inicio", "house", "Inicio"],
    ["reportes", "clipboard-list", "Reportes"],
    ["jelox", "jelox", "JELOX IA"],
    ["bandeja", "mail", "Bandeja"],
    ...(isAdmin ? [["usuarios", "user-plus", "Usuarios"] as [Tab, string, string]] : []),
    ["administrar", "menu", "Administrar"],
  ];
  return (
    <nav className="bottom-nav" style={{ gridTemplateColumns: `repeat(${tabs.length}, minmax(0, 1fr))` }}>
      {tabs.map(([key, icon, label]) => (
        <button className={tab === key ? "active" : ""} key={key} onClick={() => onChange(key)}>
          <b className={key === "jelox" ? "jelox-nav-icon" : ""}><img src={key === "jelox" ? "/jelox-welcome-hd.png" : `/icons/${icon}.svg`} alt="" /></b>
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}

