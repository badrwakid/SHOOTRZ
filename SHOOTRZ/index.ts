import './src/polyfills/crypto';
import { registerRootComponent } from 'expo';
import { LogBox } from 'react-native';

import App from './App';

// Suppress network errors in development - they're expected when backend is unavailable
if (__DEV__) {
	// Use LogBox to ignore network errors (string matching)
	LogBox.ignoreLogs([
		'Network request failed',
		'Network Error',
		'TypeError: Network request failed',
		'AuthRetryableFetchError',
		'RangeError: Failed to construct',
	]);

	// LogBox above already suppresses the network error overlays in dev mode
}

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);
