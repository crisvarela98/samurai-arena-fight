const router = require("express").Router();
const Ranking = require("../models/Ranking");

router.get("/", async (_req, res) => {
  const ranking = await Ranking.find().sort({ points: -1, wins: -1 }).limit(20);
  res.json(ranking);
});

module.exports = router;
