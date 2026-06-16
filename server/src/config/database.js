const mongoose = require("mongoose");

async function connectDatabase() {
  const allowMemoryFallback = String(process.env.ALLOW_MEMORY_DB || "").trim().toLowerCase() === "true";
  if (!process.env.MONGODB_URI) {
    if (allowMemoryFallback) {
      console.warn("MONGODB_URI is not set. Running with temporary in-memory data because ALLOW_MEMORY_DB=true.");
      return null;
    }
    throw new Error("MONGODB_URI is required. Set ALLOW_MEMORY_DB=true only for temporary local testing.");
  }
  return mongoose.connect(process.env.MONGODB_URI);
}

module.exports = { connectDatabase };
