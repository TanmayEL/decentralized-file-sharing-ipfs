const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const authRoutes = require('./routes/auth');
const fileRoutes = require('./routes/files');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');

const app = express();

// lock it down but not so hard that browsers freak out
app.use(helmet({
  crossOriginResourcePolicy: { policy: 'cross-origin' },
  crossOriginOpenerPolicy: { policy: 'same-origin-allow-popups' }
}));

app.use(cors({
  origin: [
    process.env.FRONTEND_URL || 'http://localhost:3000',
    'https://ipfs-file-sharing.netlify.app',
    'https://ipfs-file-sharing.netlify.app/',
    'http://ipfs-file-sharing.netlify.app',
    'http://ipfs-file-sharing.netlify.app/'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// 100 requests per 15 min — pretty generous, spammers stay out
const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
app.use('/api/', limiter);

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

app.get('/', (req, res) => {
  res.json({ message: 'IPFS File Sharing Backend API' });
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.use('/api', authRoutes);
app.use('/api', fileRoutes);

app.use(errorHandler);
app.use('*', notFoundHandler);

module.exports = app;
