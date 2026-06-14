const express = require("express");
const cors = require("cors");

const { corsOptions, buildAllowedOrigins } = require("./config/cors");
const usersRoutes = require("./routes/users.routes");
const roomsRoutes = require("./routes/rooms.routes");
const rankingRoutes = require("./routes/ranking.routes");
const authRoutes = require("./routes/auth.routes");

const app = express();

app.use(cors(corsOptions));
app.use(express.json());

app.get("/", (_req, res) => {
  res.json({
    ok: true,
    message: "Samurai Arena Fight server running",
  });
});

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    message: "Samurai Arena Fight server healthy",
    environment: process.env.NODE_ENV || "development",
    allowedOrigins: buildAllowedOrigins(),
  });
});

app.use("/api/users", usersRoutes);
app.use("/api/rooms", roomsRoutes);
app.use("/api/ranking", rankingRoutes);
app.use("/api/auth", authRoutes);

module.exports = { app };
