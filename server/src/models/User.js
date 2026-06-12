const mongoose = require("mongoose");

const userSchema = new mongoose.Schema(
  {
    username: { type: String, required: true, unique: true },
    coins: { type: Number, default: 0 },
    wins: { type: Number, default: 0 },
    losses: { type: Number, default: 0 },
    selectedFighter: { type: String, default: "kenji" },
  },
  { timestamps: true }
);

module.exports = mongoose.model("User", userSchema);
