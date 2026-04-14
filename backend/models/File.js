const mongoose = require('mongoose');

const fileSchema = new mongoose.Schema({
  name: { type: String, required: true },
  size: { type: Number, required: true },
  originalSize: { type: Number },
  compressed: { type: Boolean, default: false },
  type: { type: String, required: true },
  ipfsHash: { type: String, required: true, unique: true },
  uploadDate: { type: Date, default: Date.now },
  uploader: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  isPublic: { type: Boolean, default: false },
  accessList: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
  description: { type: String, default: '' },
  persistent: { type: Boolean, default: false }
});

module.exports = mongoose.model('File', fileSchema);
