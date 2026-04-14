const File = require('../models/File');
const { unpinFromIPFS } = require('./ipfsService');

const CLEANUP_INTERVAL_MS = 24 * 60 * 60 * 1000; // once a day is plenty
const RETENTION_DAYS = 7; // files live for a week unless marked persistent

const cleanupOldFiles = async () => {
  try {
    const cutoffDate = new Date(Date.now() - RETENTION_DAYS * 24 * 60 * 60 * 1000);

    const oldFiles = await File.find({
      uploadDate: { $lt: cutoffDate },
      persistent: { $ne: true }
    });

    console.log(`Cleanup: found ${oldFiles.length} expired files`);

    for (const file of oldFiles) {
      try {
        if (file.ipfsHash) {
          await unpinFromIPFS(file.ipfsHash);
          console.log(`Unpinned file: ${file.name} (${file.ipfsHash})`);
        }
        await File.findByIdAndDelete(file._id);
        console.log(`Deleted file record: ${file.name}`);
      } catch (error) {
        console.error(`Error cleaning up file ${file.name}:`, error.message);
      }
    }

    console.log(`Cleanup done. Removed ${oldFiles.length} files.`);
  } catch (error) {
    console.error('Cleanup error:', error);
  }
};

const startCleanupScheduler = () => {
  setInterval(cleanupOldFiles, CLEANUP_INTERVAL_MS);
};

module.exports = { cleanupOldFiles, startCleanupScheduler };
