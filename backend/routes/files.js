const express = require('express');
const { authenticateToken } = require('../middleware/auth');
const { upload } = require('../middleware/upload');
const {
  uploadFile,
  downloadFile,
  getFileMetadata,
  getUserFiles,
  getPublicFiles,
  shareFile,
  deleteFile,
  togglePersistence
} = require('../controllers/fileController');

const router = express.Router();

router.post('/upload', authenticateToken, upload.single('file'), uploadFile);
router.get('/file/:hash', authenticateToken, downloadFile);
router.get('/metadata/:hash', authenticateToken, getFileMetadata);
router.get('/files', authenticateToken, getUserFiles);
router.get('/public-files', getPublicFiles);
router.post('/share/:hash', authenticateToken, shareFile);
router.delete('/file/:hash', authenticateToken, deleteFile);
router.post('/file/:hash/toggle-persistence', authenticateToken, togglePersistence);

module.exports = router;
