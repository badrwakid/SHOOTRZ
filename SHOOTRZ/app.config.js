const fs = require('fs');
const path = require('path');

require('dotenv').config();

const appJsonPath = path.resolve(__dirname, 'app.json');
const config = JSON.parse(fs.readFileSync(appJsonPath, 'utf8'));

// Add environment variables to Expo config
module.exports = {
  ...config,
  expo: {
    ...config.expo,
    plugins: [...(config.expo.plugins || []), 'expo-video', 'expo-mail-composer', 'expo-web-browser'],
    extra: {
      apiUrl: process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000',
    },
  },
};
