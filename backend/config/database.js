const mongoose = require('mongoose');

// cache the connection so serverless cold starts don't reconnect every time
let cached = global._mongoConn || null;

const connectDB = async () => {
  if (cached && mongoose.connection.readyState === 1) return;

  try {
    cached = await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/ipfs-files');
    global._mongoConn = cached;
    console.log('Connected to MongoDB');
  } catch (error) {
    console.error('MongoDB connection error:', error);
    throw error;
  }
};

mongoose.connection.on('error', (err) => {
  console.error('MongoDB error:', err);
});

module.exports = connectDB;
