// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Ensure lodash and other node modules are resolved correctly
config.resolver.sourceExts.push('mjs', 'cjs');
config.resolver.extraNodeModules = {
	...config.resolver.extraNodeModules,
	lodash: require.resolve('lodash'),
};

module.exports = config;



