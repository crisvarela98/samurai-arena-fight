const router = require("express").Router();
const { authMiddleware } = require("../middleware/auth.middleware");
const { getClanRanking, getGeneralRanking } = require("../services/ranking.service");

router.get("/", authMiddleware, async (_req, res) => {
  const ranking = await getGeneralRanking(20);
  res.json(ranking);
});

router.get("/clans", authMiddleware, async (_req, res) => {
  const ranking = await getClanRanking(20);
  res.json(ranking);
});

module.exports = router;
