const router = require("express").Router();
const Room = require("../models/Room");

router.get("/", async (_req, res) => {
  const rooms = await Room.find().sort({ createdAt: -1 }).limit(20);
  res.json(rooms);
});

module.exports = router;
