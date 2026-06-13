const mongoose = require("mongoose");

const matchSchema = new mongoose.Schema(
  {
    roomCode: String,
    player1: String,
    player2: String,
    player1Clan: String,
    player2Clan: String,
    player1Weapon: String,
    player2Weapon: String,
    winner: String,
    loser: String,
    duration: Number,
  },
  { timestamps: true }
);

module.exports = mongoose.model("Match", matchSchema);
