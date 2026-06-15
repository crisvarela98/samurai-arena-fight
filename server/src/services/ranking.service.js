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

async function getGeneralRanking(limit = 20) {
  if (!databaseReady()) return [];
  return Ranking.find({}, { username: 1, clan: 1, weapon: 1, wins: 1, losses: 1, points: 1, _id: 0 })
    .sort({ points: -1, wins: -1, updatedAt: 1 })
    .limit(limit)
    .lean();
}

async function getClanRanking(limit = 20) {
  if (!databaseReady()) return [];
  return Ranking.aggregate([
    {
      $group: {
        _id: "$clan",
        points: { $sum: "$points" },
        wins: { $sum: "$wins" },
        losses: { $sum: "$losses" },
        members: { $sum: 1 },
      },
    },
    { $sort: { points: -1, wins: -1, members: -1, _id: 1 } },
    { $limit: limit },
    {
      $project: {
        _id: 0,
        clan: "$_id",
        points: 1,
        wins: 1,
        losses: 1,
        members: 1,
      },
    },
  ]);
}

module.exports = { upsertRanking, getGeneralRanking, getClanRanking };
