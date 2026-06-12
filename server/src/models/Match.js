const mongoose = require("mongoose");

const matchSchema = new mongoose.Schema(
  {
    roomCode: String,
    player1: String,
    player2: String,
    winner: String,
    loser: String,
    duration: Number,
  },
  { timestamps: true }
);

module.exports = mongoose.model("Match", matchSchema);
