const router = require("express").Router();
const User = require("../models/User");

router.get("/", async (_req, res) => {
  const users = await User.find().sort({ createdAt: -1 }).limit(20);
  res.json(users);
});

module.exports = router;
