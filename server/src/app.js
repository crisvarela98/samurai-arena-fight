const express = require("express");
const cors = require("cors");

const usersRoutes = require("./routes/users.routes");
const roomsRoutes = require("./routes/rooms.routes");
const rankingRoutes = require("./routes/ranking.routes");
const authRoutes = require("./routes/auth.routes");

const app = express();

app.use(cors({ origin: process.env.CLIENT_URL || "*", credentials: true }));
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.use("/api/users", usersRoutes);
app.use("/api/rooms", roomsRoutes);
app.use("/api/ranking", rankingRoutes);
app.use("/api/auth", authRoutes);

module.exports = { app };
