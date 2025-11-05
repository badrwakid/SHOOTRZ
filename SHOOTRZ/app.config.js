require('dotenv').config();
const config = require('./app.json');

// Add environment variables to Expo config
module.exports = {
  ...config,
  expo: {
    ...config.expo,
    extra: {
      apiUrl: process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000',
    },
  },
};
