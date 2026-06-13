const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const router = require("express").Router();

const { authMiddleware } = require("../middleware/auth.middleware");
const { createUser, findUserById, findUserByIdentity, publicUser } = require("../services/user.service");

const JWT_SECRET = process.env.JWT_SECRET || "secret_de_desarrollo";
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || "7d";

function issueToken(user) {
  const source = publicUser(user);
  return jwt.sign({ sub: source.id, username: source.username }, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
}

router.post("/register", async (req, res) => {
  try {
    const username = String(req.body.username || "").trim();
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");
    if (username.length < 3 || !email.includes("@") || password.length < 6) {
      return res.status(400).json({ message: "Usuario, email o contrasena invalidos" });
    }
    if (await findUserByIdentity(username) || await findUserByIdentity(email)) {
      return res.status(409).json({ message: "El usuario o email ya existe" });
    }
    const passwordHash = await bcrypt.hash(password, 12);
    const user = await createUser({ username, email, passwordHash });
    return res.status(201).json({ token: issueToken(user), user: publicUser(user) });
  } catch (error) {
    return res.status(500).json({ message: "No se pudo registrar la cuenta", detail: error.message });
  }
});

router.post("/login", async (req, res) => {
  try {
    const identity = String(req.body.identity || req.body.email || req.body.username || "").trim();
    const password = String(req.body.password || "");
    const user = await findUserByIdentity(identity);
    if (!user || !await bcrypt.compare(password, user.passwordHash)) {
      return res.status(401).json({ message: "Credenciales incorrectas" });
    }
    return res.json({ token: issueToken(user), user: publicUser(user) });
  } catch (error) {
    return res.status(500).json({ message: "No se pudo iniciar sesion", detail: error.message });
  }
});

router.get("/me", authMiddleware, async (req, res) => {
  const user = await findUserById(req.auth.sub);
  if (!user) return res.status(404).json({ message: "Usuario no encontrado" });
  return res.json({ user: publicUser(user) });
});

router.post("/logout", authMiddleware, (_req, res) => res.json({ ok: true }));

module.exports = router;
