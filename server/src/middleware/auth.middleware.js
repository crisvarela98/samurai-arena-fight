const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET || "secret_de_desarrollo";

function extractToken(req) {
  const header = req.headers.authorization || "";
  return header.startsWith("Bearer ") ? header.slice(7) : null;
}

function verifyToken(token) {
  if (!token) throw new Error("Token requerido");
  return jwt.verify(token, JWT_SECRET);
}

function authMiddleware(req, res, next) {
  try {
    req.auth = verifyToken(extractToken(req));
    next();
  } catch (_error) {
    res.status(401).json({ message: "Sesion invalida o vencida" });
  }
}

module.exports = { authMiddleware, verifyToken };
