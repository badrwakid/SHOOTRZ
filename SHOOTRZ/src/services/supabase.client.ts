import { createClient } from '@supabase/supabase-js'
import AsyncStorage from '@react-native-async-storage/async-storage'

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL as string
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY as string

// Validate environment variables
if (!supabaseUrl || !supabaseAnonKey) {
	const missing = [];
	if (!supabaseUrl) missing.push('EXPO_PUBLIC_SUPABASE_URL');
	if (!supabaseAnonKey) missing.push('EXPO_PUBLIC_SUPABASE_ANON_KEY');
	
	const errorMsg = `Missing required environment variables: ${missing.join(', ')}\n\n` +
		'Please set these in your .env file or run setup_env.ps1';
	
	console.error('❌', errorMsg);
	
	// BUG FIX: Always throw on missing env vars, not just in __DEV__
	// In production, createClient with undefined args causes cryptic runtime failures
	throw new Error(errorMsg);
}

// AsyncStorage adapter for Supabase session persistence in React Native
// This ensures sessions persist across app restarts
const AsyncStorageAdapter = {
	getItem: async (key: string): Promise<string | null> => {
		try {
			return await AsyncStorage.getItem(key);
		} catch (error) {
			console.error('❌ Error getting item from AsyncStorage:', error);
			return null;
		}
	},
	setItem: async (key: string, value: string): Promise<void> => {
		try {
			await AsyncStorage.setItem(key, value);
		} catch (error) {
			console.error('❌ Error setting item in AsyncStorage:', error);
		}
	},
	removeItem: async (key: string): Promise<void> => {
		try {
			await AsyncStorage.removeItem(key);
		} catch (error) {
			console.error('❌ Error removing item from AsyncStorage:', error);
		}
	},
};

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
	auth: {
		autoRefreshToken: true,
		persistSession: true, // Enable session persistence
		detectSessionInUrl: false, // Disable URL detection for React Native
		// For React Native OAuth
		flowType: 'pkce',
		// Use AsyncStorage adapter for React Native session persistence
		// This ensures sessions are saved and restored when app restarts
		storage: AsyncStorageAdapter,
	},
})
