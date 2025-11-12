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

	// Intercept console.error to suppress network errors
	const originalError = console.error;
	console.error = (...args: any[]) => {
		const message = args.join(' ');
		const isNetworkError =
			message.includes('Network request failed') ||
			message.includes('Network Error') ||
			message.includes('TypeError: Network request failed') ||
			message.includes('AuthRetryableFetchError') ||
			message.includes('RangeError: Failed to construct \'Response\'') ||
			(message.includes('TypeError') && message.includes('Network')) ||
			(message.includes('AuthRetryableFetchError') && message.includes('Network'));

		if (!isNetworkError) {
			originalError.apply(console, args);
		}
		// Silently ignore network errors
	};
}

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);
