const fs = require('fs');
const os = require('os');
const path = require('path');

function findLocalIp() {
  const interfaces = os.networkInterfaces();
  const candidates = [];

  Object.entries(interfaces).forEach(([name, infos]) => {
    if (!infos) return;
    infos.forEach((info) => {
      if (info.family !== 'IPv4' || info.internal) {
        return;
      }

      candidates.push({
        name,
        address: info.address,
      });
    });
  });

  if (candidates.length === 0) {
    return null;
  }

  // Prefer Wi-Fi / WLAN / Wireless interfaces if present
  const wifiCandidate = candidates.find(({ name }) =>
    /wi[-]?fi|wlan|wireless/i.test(name)
  );

  return (wifiCandidate || candidates[0]).address;
}

function updateEnvFile(envPath, newUrl) {
  let contents = '';
  if (fs.existsSync(envPath)) {
    contents = fs.readFileSync(envPath, 'utf8');
  }

  const lines = contents.split(/\r?\n/).filter((line) => line.trim().length > 0);
  const targetKey = 'EXPO_PUBLIC_API_URL';
  let found = false;

  const updatedLines = lines.map((line) => {
    if (line.trim().startsWith(`${targetKey}=`)) {
      found = true;
      return `${targetKey}=${newUrl}`;
    }
    return line;
  });

  if (!found) {
    updatedLines.push(`${targetKey}=${newUrl}`);
  }

  fs.writeFileSync(envPath, `${updatedLines.join('\n')}\n`, 'utf8');
}

function main() {
  const localIp = findLocalIp();

  if (!localIp) {
    console.warn('[set-expo-ip] Could not determine local network IP address.');
    console.warn('[set-expo-ip] Expo will continue using the existing EXPO_PUBLIC_API_URL value.');
    process.exit(0);
  }

  const apiUrl = `http://${localIp}:8000`;
  const envPath = path.resolve(__dirname, '..', '.env');

  try {
    updateEnvFile(envPath, apiUrl);
    console.log(`[set-expo-ip] Updated EXPO_PUBLIC_API_URL to ${apiUrl}`);
  } catch (error) {
    console.error('[set-expo-ip] Failed to update .env file:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
