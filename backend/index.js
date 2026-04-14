require('dotenv').config();
const app = require('./app');
const connectDB = require('./config/database');
const { startCleanupScheduler } = require('./services/cleanupService');

const PORT = process.env.PORT || 5000;

// connect at startup — cached so serverless re-invocations skip reconnecting
connectDB();

// setInterval doesn't survive serverless cold starts on Vercel
// for production cleanup, use a Vercel Cron Job pointing at /api/cleanup
if (process.env.NODE_ENV !== 'production') {
  startCleanupScheduler();
}

app.listen(PORT, () => {
  console.log(`Server up on port ${PORT}`);
});

module.exports = app; // Vercel uses this as the serverless handler
