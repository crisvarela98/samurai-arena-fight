const Ranking = require("../models/Ranking");
const Match = require("../models/Match");
const User = require("../models/User");
const { databaseReady } = require("./user.service");

const RANKING_POINTS_PER_WIN = 10;
const HONOR_POINTS_PER_WIN = 10;

async function upsertRanking(winner, loser) {
  if (!databaseReady()) return;
  const winnerUsername = winner?.username;
  const loserUsername = loser?.username;
  if (winnerUsername) {
    await Ranking.findOneAndUpdate(
      { username: winnerUsername },
      {
        $inc: { wins: 1, points: RANKING_POINTS_PER_WIN },
        $set: { clan: winner.clanId, weapon: winner.weaponId },
        $setOnInsert: { username: winnerUsername, userId: winner.userId || null },
      },
      { upsert: true, new: true }
    );
    if (winner.userId) {
      await User.findByIdAndUpdate(winner.userId, {
        $inc: { wins: 1, rankingPoints: RANKING_POINTS_PER_WIN, honorPoints: HONOR_POINTS_PER_WIN },
      });
    }
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

function normalizeRankingRange(range) {
  const value = String(range || "global").trim().toLowerCase();
  return ["today", "week", "global"].includes(value) ? value : "global";
}

function clampTimezoneOffset(offset) {
  const numeric = Number(offset);
  return Number.isFinite(numeric) ? Math.max(-840, Math.min(840, numeric)) : 0;
}

function buildRangeStart(range, tzOffsetMinutes = 0) {
  const normalizedRange = normalizeRankingRange(range);
  if (normalizedRange === "global") return null;

  const offset = clampTimezoneOffset(tzOffsetMinutes);
  const now = new Date();
  const adjustedNow = new Date(now.getTime() - offset * 60_000);
  const startOfDeviceDay = new Date(
    Date.UTC(adjustedNow.getUTCFullYear(), adjustedNow.getUTCMonth(), adjustedNow.getUTCDate())
  );

  if (normalizedRange === "today") {
    return new Date(startOfDeviceDay.getTime() + offset * 60_000);
  }

  const sevenDayStart = new Date(startOfDeviceDay.getTime() - 6 * 24 * 60 * 60 * 1000);
  return new Date(sevenDayStart.getTime() + offset * 60_000);
}

function buildGeneralMatchAggregation(limit, range, tzOffsetMinutes) {
  const matchFilter = {};
  const rangeStart = buildRangeStart(range, tzOffsetMinutes);
  if (rangeStart) {
    matchFilter.createdAt = { $gte: rangeStart };
  }

  const pipeline = [
    { $match: matchFilter },
    {
      $project: {
        createdAt: 1,
        participants: [
          {
            username: "$player1",
            clan: "$player1Clan",
            weapon: "$player1Weapon",
            result: {
              $cond: [{ $eq: ["$winner", "$player1"] }, "win", "loss"],
            },
          },
          {
            username: "$player2",
            clan: "$player2Clan",
            weapon: "$player2Weapon",
            result: {
              $cond: [{ $eq: ["$winner", "$player2"] }, "win", "loss"],
            },
          },
        ],
      },
    },
    { $unwind: "$participants" },
    { $sort: { createdAt: -1 } },
    {
      $group: {
        _id: "$participants.username",
        username: { $first: "$participants.username" },
        clan: { $first: "$participants.clan" },
        weapon: { $first: "$participants.weapon" },
        wins: {
          $sum: {
            $cond: [{ $eq: ["$participants.result", "win"] }, 1, 0],
          },
        },
        losses: {
          $sum: {
            $cond: [{ $eq: ["$participants.result", "loss"] }, 1, 0],
          },
        },
        points: {
          $sum: {
            $cond: [{ $eq: ["$participants.result", "win"] }, RANKING_POINTS_PER_WIN, 0],
          },
        },
        lastMatchAt: { $max: "$createdAt" },
      },
    },
    { $sort: { points: -1, wins: -1, lastMatchAt: 1, username: 1 } },
    { $project: { _id: 0, lastMatchAt: 0 } },
  ];

  if (Number.isFinite(limit) && limit > 0) {
    pipeline.splice(-1, 0, { $limit: limit });
  }

  return pipeline;
}

function buildClanMatchAggregation(limit, range, tzOffsetMinutes) {
  const matchFilter = {};
  const rangeStart = buildRangeStart(range, tzOffsetMinutes);
  if (rangeStart) {
    matchFilter.createdAt = { $gte: rangeStart };
  }

  const pipeline = [
    { $match: matchFilter },
    {
      $project: {
        participants: [
          {
            username: "$player1",
            clan: "$player1Clan",
            wins: { $cond: [{ $eq: ["$winner", "$player1"] }, 1, 0] },
            losses: { $cond: [{ $eq: ["$winner", "$player1"] }, 0, 1] },
            points: { $cond: [{ $eq: ["$winner", "$player1"] }, RANKING_POINTS_PER_WIN, 0] },
          },
          {
            username: "$player2",
            clan: "$player2Clan",
            wins: { $cond: [{ $eq: ["$winner", "$player2"] }, 1, 0] },
            losses: { $cond: [{ $eq: ["$winner", "$player2"] }, 0, 1] },
            points: { $cond: [{ $eq: ["$winner", "$player2"] }, RANKING_POINTS_PER_WIN, 0] },
          },
        ],
      },
    },
    { $unwind: "$participants" },
    {
      $group: {
        _id: "$participants.clan",
        points: { $sum: "$participants.points" },
        wins: { $sum: "$participants.wins" },
        losses: { $sum: "$participants.losses" },
        membersSet: { $addToSet: "$participants.username" },
      },
    },
    {
      $project: {
        _id: 0,
        clan: "$_id",
        points: 1,
        wins: 1,
        losses: 1,
        members: { $size: "$membersSet" },
      },
    },
    { $sort: { points: -1, wins: -1, members: -1, clan: 1 } },
  ];

  if (Number.isFinite(limit) && limit > 0) {
    pipeline.push({ $limit: limit });
  }

  return pipeline;
}

async function getGeneralRankingRows(limit = 20, options = {}) {
  if (!databaseReady()) return [];
  const range = normalizeRankingRange(options.range);
  if (range !== "global") {
    return Match.aggregate(buildGeneralMatchAggregation(limit, range, options.tzOffsetMinutes));
  }

  const query = Ranking.find({}, { username: 1, clan: 1, weapon: 1, wins: 1, losses: 1, points: 1, _id: 0 })
    .sort({ points: -1, wins: -1, updatedAt: 1, username: 1 });

  if (Number.isFinite(limit) && limit > 0) {
    query.limit(limit);
  }

  return query.lean();
}

async function getClanRankingRows(limit = 20, options = {}) {
  if (!databaseReady()) return [];
  const range = normalizeRankingRange(options.range);
  if (range !== "global") {
    return Match.aggregate(buildClanMatchAggregation(limit, range, options.tzOffsetMinutes));
  }

  const pipeline = [
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
  ];

  if (Number.isFinite(limit) && limit > 0) {
    pipeline.splice(2, 0, { $limit: limit });
  }

  return Ranking.aggregate(pipeline);
}

function buildPositionSummary(rows, indexKey, value) {
  const normalizedValue = String(value || "").trim();
  if (!normalizedValue) return null;

  const entryIndex = rows.findIndex((row) => String(row[indexKey] || "").toLowerCase() === normalizedValue.toLowerCase());
  const positionKey = indexKey === "clan" ? "totalClans" : "totalPlayers";
  const base = entryIndex >= 0 ? rows[entryIndex] : { [indexKey]: normalizedValue };

  return {
    ...base,
    position: entryIndex >= 0 ? entryIndex + 1 : null,
    [positionKey]: rows.length,
  };
}

async function getGeneralRanking(limit = 20, options = {}) {
  return getGeneralRankingRows(limit, options);
}

async function getClanRanking(limit = 20, options = {}) {
  return getClanRankingRows(limit, options);
}

async function getRankingSummary(options = {}) {
  if (!databaseReady()) {
    return {
      range: normalizeRankingRange(options.range),
      player: null,
      clan: null,
    };
  }

  const [generalRows, clanRows] = await Promise.all([
    getGeneralRankingRows(null, options),
    getClanRankingRows(null, options),
  ]);

  return {
    range: normalizeRankingRange(options.range),
    player: buildPositionSummary(generalRows, "username", options.username),
    clan: buildPositionSummary(clanRows, "clan", options.clan),
  };
}

module.exports = {
  upsertRanking,
  getGeneralRanking,
  getClanRanking,
  getRankingSummary,
  normalizeRankingRange,
};
