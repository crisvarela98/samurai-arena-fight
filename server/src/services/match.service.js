const Match = require("../models/Match");

async function saveMatchResult(payload) {
  try {
    return await Match.create(payload);
  } catch (error) {
    return null;
  }
}

module.exports = { saveMatchResult };
