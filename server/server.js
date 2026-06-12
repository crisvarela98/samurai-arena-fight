require("dotenv").config();

const { createServer } = require("http");
const { app } = require("./src/app");
const { initSocket } = require("./src/socket");
const { connectDatabase } = require("./src/config/database");

const port = process.env.PORT || 3000;
const server = createServer(app);

initSocket(server);

connectDatabase()
  .then(() => {
    server.listen(port, () => {
      console.log(`Server running on port ${port}`);
    });
  })
  .catch((error) => {
    console.error("Database connection error:", error.message);
    process.exit(1);
  });
