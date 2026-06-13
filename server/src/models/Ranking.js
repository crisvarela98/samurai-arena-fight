const mongoose = require("mongoose");

const rankingSchema = new mongoose.Schema(
  {
    userId: { type: mongoose.Schema.Types.ObjectId, ref: "User", default: null },
    username: { type: String, required: true, unique: true },
    clan: { type: String, default: "cuervo_negro" },
    weapon: { type: String, default: "katana" },
    wins: { type: Number, default: 0 },
    losses: { type: Number, default: 0 },
    points: { type: Number, default: 0 },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Ranking", rankingSchema);
