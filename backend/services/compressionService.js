const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const zlib = require('zlib');

const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];
const MIN_SIZE_FOR_COMPRESSION = 1024 * 1024; // don't bother under 1MB, not worth it
const IMAGE_COMPRESSION_THRESHOLD = 0.9;      // only keep if actually smaller
const GZIP_COMPRESSION_THRESHOLD = 0.8;       // gzip needs to earn it — 20% savings minimum

const compressImage = async (filePath, compressedPath, fileSize) => {
  await sharp(filePath)
    .jpeg({ quality: 80, progressive: true })
    .png({ compressionLevel: 8 })
    .webp({ quality: 80 })
    .toFile(compressedPath);

  const compressedStats = fs.statSync(compressedPath);
  const compressionRatio = (1 - compressedStats.size / fileSize) * 100;
  console.log(`Image: ${(fileSize / 1024 / 1024).toFixed(2)}MB → ${(compressedStats.size / 1024 / 1024).toFixed(2)}MB (${compressionRatio.toFixed(1)}% smaller)`);

  if (compressedStats.size < fileSize * IMAGE_COMPRESSION_THRESHOLD) {
    fs.unlinkSync(filePath);
    return { filePath: compressedPath, compressed: true, originalSize: fileSize, compressedSize: compressedStats.size };
  }

  // not worth it — just use the original
  fs.unlinkSync(compressedPath);
  return { filePath, compressed: false, originalSize: fileSize };
};

const compressWithGzip = async (filePath, compressedPath, fileSize) => {
  const gzip = zlib.createGzip();
  const input = fs.createReadStream(filePath);
  const output = fs.createWriteStream(compressedPath);

  await new Promise((resolve, reject) => {
    input.pipe(gzip).pipe(output);
    output.on('finish', resolve);
    output.on('error', reject);
  });

  const compressedStats = fs.statSync(compressedPath);
  const compressionRatio = (1 - compressedStats.size / fileSize) * 100;
  console.log(`File: ${(fileSize / 1024 / 1024).toFixed(2)}MB → ${(compressedStats.size / 1024 / 1024).toFixed(2)}MB (${compressionRatio.toFixed(1)}% smaller)`);

  if (compressedStats.size < fileSize * GZIP_COMPRESSION_THRESHOLD) {
    fs.unlinkSync(filePath);
    return { filePath: compressedPath, compressed: true, originalSize: fileSize, compressedSize: compressedStats.size };
  }

  fs.unlinkSync(compressedPath);
  return { filePath, compressed: false, originalSize: fileSize };
};

const compressFile = async (filePath, originalName) => {
  try {
    const stats = fs.statSync(filePath);
    const fileSize = stats.size;

    if (fileSize < MIN_SIZE_FOR_COMPRESSION) {
      return { filePath, compressed: false, originalSize: fileSize };
    }

    const ext = path.extname(originalName).toLowerCase();
    const compressedPath = filePath + '.compressed';

    if (IMAGE_EXTENSIONS.includes(ext)) {
      return await compressImage(filePath, compressedPath, fileSize);
    }

    return await compressWithGzip(filePath, compressedPath, fileSize);
  } catch (error) {
    console.error('Compression failed, sending original:', error);
    return { filePath, compressed: false, originalSize: fs.statSync(filePath).size };
  }
};

module.exports = { compressFile };
