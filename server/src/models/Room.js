const mongoose = require("mongoose");

const roomSchema = new mongoose.Schema(
  {
    roomCode: { type: String, required: true, unique: true },
    players: [
      {
        userId: { type: mongoose.Schema.Types.ObjectId, ref: "User", default: null },
        username: String,
        clanId: String,
        weaponId: String,
        color: [Number],
      },
    ],
    status: { type: String, enum: ["waiting", "fighting", "finished"], default: "waiting" },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Room", roomSchema);
