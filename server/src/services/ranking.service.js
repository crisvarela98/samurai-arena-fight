const Ranking = require("../models/Ranking");

async function upsertRanking(winnerUsername, loserUsername) {
  if (winnerUsername) {
    await Ranking.findOneAndUpdate(
      { username: winnerUsername },
      { $inc: { wins: 1, points: 10 }, $setOnInsert: { username: winnerUsername } },
      { upsert: true, new: true }
    );
  }
  if (loserUsername) {
    await Ranking.findOneAndUpdate(
      { username: loserUsername },
      { $inc: { losses: 1 }, $setOnInsert: { username: loserUsername } },
      { upsert: true, new: true }
    );
  }
}

module.exports = { upsertRanking };
