const router = require("express").Router();
const { authMiddleware } = require("../middleware/auth.middleware");
const { listRooms } = require("../services/room.service");

router.get("/", authMiddleware, async (_req, res) => {
  res.json(await listRooms());
});

module.exports = router;
