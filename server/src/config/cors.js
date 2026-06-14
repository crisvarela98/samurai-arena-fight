function normalizeOrigin(origin) {
  return String(origin || "").replace(/\/+$/, "");
}

function parseConfiguredOrigins(value) {
  return String(value || "")
    .split(",")
    .map((item) => normalizeOrigin(item.trim()))
    .filter(Boolean);
}

function buildAllowedOrigins() {
  const configuredOrigins = parseConfiguredOrigins(process.env.CLIENT_URL);
  if (process.env.NODE_ENV === "production") {
    return configuredOrigins;
  }
  return [...new Set([
    ...configuredOrigins,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
  ])];
}

function isOriginAllowed(origin) {
  if (!origin) return true;
  const allowedOrigins = buildAllowedOrigins();
  if (!allowedOrigins.length) {
    return process.env.NODE_ENV !== "production";
  }
  return allowedOrigins.includes(normalizeOrigin(origin));
}

const corsOptions = {
  origin(origin, callback) {
    if (isOriginAllowed(origin)) {
      callback(null, true);
      return;
    }
    callback(new Error("CORS origin blocked"));
  },
  credentials: true,
};

const socketCorsOptions = {
  origin(origin, callback) {
    if (isOriginAllowed(origin)) {
      callback(null, true);
      return;
    }
    callback(new Error("Socket.IO CORS origin blocked"));
  },
  credentials: true,
};

module.exports = {
  buildAllowedOrigins,
  corsOptions,
  socketCorsOptions,
};
