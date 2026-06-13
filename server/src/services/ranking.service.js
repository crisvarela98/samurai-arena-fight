const Ranking = require("../models/Ranking");
const User = require("../models/User");
const { databaseReady } = require("./user.service");

async function upsertRanking(winner, loser) {
  if (!databaseReady()) return;
  const winnerUsername = winner?.username;
  const loserUsername = loser?.username;
  if (winnerUsername) {
    await Ranking.findOneAndUpdate(
      { username: winnerUsername },
      {
        $inc: { wins: 1, points: 10 },
        $set: { clan: winner.clanId, weapon: winner.weaponId },
        $setOnInsert: { username: winnerUsername, userId: winner.userId || null },
      },
      { upsert: true, new: true }
    );
    if (winner.userId) await User.findByIdAndUpdate(winner.userId, { $inc: { wins: 1, rankingPoints: 10 } });
  }
  if (loserUsername) {
    await Ranking.findOneAndUpdate(
      { username: loserUsername },
      {
        $inc: { losses: 1 },
        $set: { clan: loser.clanId, weapon: loser.weaponId },
        $setOnInsert: { username: loserUsername, userId: loser.userId || null },
      },
      { upsert: true, new: true }
    );
    if (loser.userId) await User.findByIdAndUpdate(loser.userId, { $inc: { losses: 1 } });
  }
}

module.exports = { upsertRanking };
