const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const getPinataHeaders = () => ({
  'pinata_api_key': process.env.PINATA_API_KEY,
  'pinata_secret_api_key': process.env.PINATA_SECRET_KEY
});

const uploadToIPFS = async (filePath, originalName, compressed) => {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));
  formData.append('pinataMetadata', JSON.stringify({ name: originalName, compressed }));
  formData.append('pinataOptions', JSON.stringify({ cidVersion: 0 }));

  const response = await axios.post('https://api.pinata.cloud/pinning/pinFileToIPFS', formData, {
    headers: {
      ...getPinataHeaders(),
      ...formData.getHeaders()
    }
  });

  return response.data.IpfsHash;
};

const unpinFromIPFS = async (ipfsHash) => {
  await axios.delete(`https://api.pinata.cloud/pinning/unpin/${ipfsHash}`, {
    headers: getPinataHeaders()
  });
};

const getGatewayUrl = (ipfsHash) => `https://gateway.pinata.cloud/ipfs/${ipfsHash}`;

const isPinataConfigured = () =>
  Boolean(process.env.PINATA_API_KEY && process.env.PINATA_SECRET_KEY);

module.exports = { uploadToIPFS, unpinFromIPFS, getGatewayUrl, isPinataConfigured };
