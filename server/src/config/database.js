const mongoose = require("mongoose");

async function connectDatabase() {
  if (!process.env.MONGODB_URI) {
    console.warn("MONGODB_URI is not set. Server will run without DB persistence.");
    return null;
  }
  return mongoose.connect(process.env.MONGODB_URI);
}

module.exports = { connectDatabase };
