const fs = require('fs');
const File = require('../models/File');
const User = require('../models/User');
const { compressFile } = require('../services/compressionService');
const { uploadToIPFS, getGatewayUrl, isPinataConfigured } = require('../services/ipfsService');

const uploadFile = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    if (req.file.size > 10 * 1024 * 1024) {
      fs.unlinkSync(req.file.path);
      return res.status(400).json({ error: 'File size exceeds 10MB limit' });
    }

    if (!isPinataConfigured()) {
      return res.status(500).json({ error: 'Pinata configuration not available' });
    }

    const { isPublic, description } = req.body;

    console.log(`Compressing file: ${req.file.originalname} (${(req.file.size / 1024 / 1024).toFixed(2)}MB)`);
    const compressionResult = await compressFile(req.file.path, req.file.originalname);
    const finalSize = compressionResult.compressedSize || compressionResult.originalSize;

    const ipfsHash = await uploadToIPFS(compressionResult.filePath, req.file.originalname, compressionResult.compressed);

    const file = new File({
      name: req.file.originalname,
      size: finalSize,
      originalSize: compressionResult.originalSize,
      compressed: compressionResult.compressed,
      type: req.file.mimetype,
      ipfsHash,
      uploader: req.user.userId,
      isPublic: isPublic === 'true',
      description: description || ''
    });

    await file.save();
    await User.findByIdAndUpdate(req.user.userId, { $push: { files: file._id } });

    fs.unlinkSync(compressionResult.filePath);

    res.json({
      message: 'File uploaded successfully',
      file: {
        id: file._id,
        name: file.name,
        size: file.size,
        type: file.type,
        ipfsHash: file.ipfsHash,
        uploadDate: file.uploadDate,
        isPublic: file.isPublic,
        description: file.description
      }
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'File upload failed' });
  }
};

const downloadFile = async (req, res) => {
  try {
    const { hash } = req.params;
    const file = await File.findOne({ ipfsHash: hash }).populate('uploader');

    if (!file) {
      return res.status(404).json({ error: 'File not found' });
    }

    const hasAccess = file.isPublic ||
      file.uploader._id.toString() === req.user.userId ||
      file.accessList.includes(req.user.userId);

    if (!hasAccess) {
      return res.status(403).json({ error: 'Access denied' });
    }

    res.redirect(getGatewayUrl(hash));
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({ error: 'File download failed' });
  }
};

const getFileMetadata = async (req, res) => {
  try {
    const { hash } = req.params;
    const file = await File.findOne({ ipfsHash: hash }).populate('uploader');

    if (!file) {
      return res.status(404).json({ error: 'File not found' });
    }

    const hasAccess = file.isPublic ||
      file.uploader._id.toString() === req.user.userId ||
      file.accessList.includes(req.user.userId);

    if (!hasAccess) {
      return res.status(403).json({ error: 'Access denied' });
    }

    res.json({
      id: file._id,
      name: file.name,
      size: file.size,
      type: file.type,
      ipfsHash: file.ipfsHash,
      uploadDate: file.uploadDate,
      uploader: { id: file.uploader._id, username: file.uploader.username },
      isPublic: file.isPublic,
      description: file.description
    });
  } catch (error) {
    console.error('Metadata error:', error);
    res.status(500).json({ error: 'Failed to get file metadata' });
  }
};

const getUserFiles = async (req, res) => {
  try {
    const files = await File.find({
      $or: [{ uploader: req.user.userId }, { accessList: req.user.userId }]
    }).populate('uploader', 'username').sort({ uploadDate: -1 });

    res.json({ files });
  } catch (error) {
    console.error('Files error:', error);
    res.status(500).json({ error: 'Failed to get files' });
  }
};

const getPublicFiles = async (req, res) => {
  try {
    const files = await File.find({ isPublic: true })
      .populate('uploader', 'username')
      .sort({ uploadDate: -1 })
      .limit(50);

    res.json({ files });
  } catch (error) {
    console.error('Public files error:', error);
    res.status(500).json({ error: 'Failed to get public files' });
  }
};

const shareFile = async (req, res) => {
  try {
    const { hash } = req.params;
    const { userIds } = req.body;

    const file = await File.findOne({ ipfsHash: hash });

    if (!file) {
      return res.status(404).json({ error: 'File not found' });
    }

    if (file.uploader.toString() !== req.user.userId) {
      return res.status(403).json({ error: 'Only file owner can share' });
    }

    file.accessList = [...new Set([...file.accessList, ...userIds])];
    await file.save();

    res.json({ message: 'File shared successfully' });
  } catch (error) {
    console.error('Share error:', error);
    res.status(500).json({ error: 'Failed to share file' });
  }
};

const deleteFile = async (req, res) => {
  try {
    const { hash } = req.params;
    const file = await File.findOne({ ipfsHash: hash });

    if (!file) {
      return res.status(404).json({ error: 'File not found' });
    }

    if (file.uploader.toString() !== req.user.userId) {
      return res.status(403).json({ error: 'Only file owner can delete' });
    }

    await User.findByIdAndUpdate(req.user.userId, { $pull: { files: file._id } });
    await File.findByIdAndDelete(file._id);

    res.json({ message: 'File deleted successfully' });
  } catch (error) {
    console.error('Delete error:', error);
    res.status(500).json({ error: 'Failed to delete file' });
  }
};

const togglePersistence = async (req, res) => {
  try {
    const { hash } = req.params;
    const file = await File.findOne({ ipfsHash: hash });

    if (!file) {
      return res.status(404).json({ error: 'File not found' });
    }

    if (file.uploader.toString() !== req.user.userId) {
      return res.status(403).json({ error: 'Only file owner can modify persistence' });
    }

    file.persistent = !file.persistent;
    await file.save();

    res.json({
      message: `File persistence ${file.persistent ? 'enabled' : 'disabled'}`,
      persistent: file.persistent
    });
  } catch (error) {
    console.error('Toggle persistence error:', error);
    res.status(500).json({ error: 'Failed to toggle file persistence' });
  }
};

module.exports = {
  uploadFile,
  downloadFile,
  getFileMetadata,
  getUserFiles,
  getPublicFiles,
  shareFile,
  deleteFile,
  togglePersistence
};
