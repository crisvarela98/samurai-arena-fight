const mongoose = require("mongoose");

const userSchema = new mongoose.Schema(
  {
    username: { type: String, required: true, unique: true, trim: true },
    email: { type: String, required: true, unique: true, trim: true, lowercase: true },
    passwordHash: { type: String, required: true },
    coins: { type: Number, default: 0 },
    wins: { type: Number, default: 0 },
    losses: { type: Number, default: 0 },
    rankingPoints: { type: Number, default: 0 },
    selectedClan: { type: String, default: "cuervo_negro" },
    selectedWeapon: { type: String, default: "katana" },
    selectedColor: { type: [Number], default: [170, 48, 52] },
    storyProgress: { type: mongoose.Schema.Types.Mixed, default: {} },
    unlockedClans: { type: [String], default: ["cuervo_negro"] },
    unlockedWeapons: { type: [String], default: ["katana"] },
  },
  { timestamps: true }
);

module.exports = mongoose.model("User", userSchema);
