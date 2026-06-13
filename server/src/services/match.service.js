const Match = require("../models/Match");
const { databaseReady } = require("./user.service");

async function saveMatchResult(payload) {
  if (!databaseReady()) return null;
  try {
    return await Match.create(payload);
  } catch (error) {
    return null;
  }
}

module.exports = { saveMatchResult };
