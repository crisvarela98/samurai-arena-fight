const router = require("express").Router();
const User = require("../models/User");
const { authMiddleware } = require("../middleware/auth.middleware");
const { databaseReady, updateUser, publicUser } = require("../services/user.service");

router.get("/", authMiddleware, async (_req, res) => {
  if (!databaseReady()) return res.json([]);
  const users = await User.find().sort({ createdAt: -1 }).limit(20);
  res.json(users.map(publicUser));
});

router.put("/me/progress", authMiddleware, async (req, res) => {
  const changes = {
    storyProgress: req.body.storyProgress || {},
    coins: Number(req.body.coins || 0),
    selectedClan: req.body.selectedClan || "cuervo_negro",
    selectedWeapon: req.body.selectedWeapon || "katana",
    selectedColor: req.body.selectedColor || [170, 48, 52],
  };
  const user = await updateUser(req.auth.sub, changes);
  res.json({ user: publicUser(user) });
});

module.exports = router;
