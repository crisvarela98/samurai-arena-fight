const mongoose = require("mongoose");

const roomSchema = new mongoose.Schema(
  {
    roomCode: { type: String, required: true, unique: true },
    players: [{ type: String }],
    status: { type: String, enum: ["waiting", "fighting", "finished"], default: "waiting" },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Room", roomSchema);
