const router = require("express").Router();
const Ranking = require("../models/Ranking");
const { authMiddleware } = require("../middleware/auth.middleware");
const { databaseReady } = require("../services/user.service");

router.get("/", authMiddleware, async (_req, res) => {
  if (!databaseReady()) return res.json([]);
  const ranking = await Ranking.find().sort({ points: -1, wins: -1 }).limit(20);
  res.json(ranking);
});

module.exports = router;
