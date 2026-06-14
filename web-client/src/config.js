const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1"]);

function stripTrailingSlash(value) {
  return String(value || "").replace(/\/+$/, "");
}

function defaultOrigin() {
  if (LOCAL_HOSTS.has(window.location.hostname)) {
    return "http://localhost:3000";
  }
  return stripTrailingSlash(window.location.origin);
}

export function resolveRuntimeConfig(settings = {}) {
  const runtime = window.SAMURAI_CONFIG || {};
  const serverUrl = stripTrailingSlash(
    settings.serverUrl ||
      import.meta.env.VITE_SERVER_URL ||
      runtime.SERVER_URL ||
      runtime.API_BASE_URL ||
      defaultOrigin(),
  );
  const apiBaseUrl = stripTrailingSlash(
    settings.apiBaseUrl ||
      import.meta.env.VITE_API_BASE_URL ||
      runtime.API_BASE_URL ||
      serverUrl,
  );
  const socketUrl = stripTrailingSlash(
    settings.socketUrl ||
      import.meta.env.VITE_SOCKET_URL ||
      runtime.SOCKET_URL ||
      serverUrl,
  );
  return {
    serverUrl,
    apiBaseUrl,
    socketUrl,
    isProductionHost: !LOCAL_HOSTS.has(window.location.hostname),
  };
}
