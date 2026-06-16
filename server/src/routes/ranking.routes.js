const router = require("express").Router();
const { authMiddleware } = require("../middleware/auth.middleware");
const { getClanRanking, getGeneralRanking, getRankingSummary, normalizeRankingRange } = require("../services/ranking.service");

function requestOptions(req) {
  return {
    range: normalizeRankingRange(req.query.range),
    tzOffsetMinutes: Number(req.query.tzOffsetMinutes),
  };
}

router.get("/", authMiddleware, async (req, res) => {
  const ranking = await getGeneralRanking(20, requestOptions(req));
  res.json(ranking);
});

router.get("/clans", authMiddleware, async (req, res) => {
  const ranking = await getClanRanking(20, requestOptions(req));
  res.json(ranking);
});

router.get("/summary", authMiddleware, async (req, res) => {
  const ranking = await getRankingSummary({
    ...requestOptions(req),
    username: String(req.query.username || req.user?.username || "").trim(),
    clan: String(req.query.clan || "").trim(),
  });
  res.json(ranking);
});

module.exports = router;
