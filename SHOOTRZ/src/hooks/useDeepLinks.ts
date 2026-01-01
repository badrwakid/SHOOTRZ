import { useEffect } from 'react';
import { Alert } from 'react-native';
import * as Linking from 'expo-linking';
import { parseDeepLink } from '../utils/deepLinks';
import { supabase } from '../services/supabase.client';

/**
 * Hook to handle deep links for authentication flows
 * Handles: password reset, email confirmation, OAuth callbacks
 */
export function useDeepLinks(onHandled?: () => void) {
	useEffect(() => {
		const handleDeepLink = async (url: string) => {
			// Skip processing base exp:// URLs (just app start, not actual deep links)
			if (url.match(/^exp:\/\/[\d.]+:\d+$/)) {
				return;
			}
			
			// CRITICAL: Check if this URL contains an OAuth code even before parsing
			if (url.includes('code=')) {
				console.log('🔗 Processing OAuth callback:', url.substring(0, 100) + '...');
			}
			
			let params;
			try {
				params = parseDeepLink(url);
			} catch (parseError) {
				console.error('❌ Error parsing deep link:', parseError);
				// Even if parsing fails, try to extract code directly if present
				if (url.includes('code=')) {
					console.log('⚠️ Parser failed but code detected, attempting direct extraction...');
					const codeMatch = url.match(/[?&#]code=([^&#]+)/);
					if (codeMatch) {
						const code = decodeURIComponent(codeMatch[1]);
						console.log('✅ Extracted code directly, attempting session exchange...');
						try {
							const { data, error } = await supabase.auth.exchangeCodeForSession(code);
							if (error) {
								console.error('❌ Direct code exchange failed:', error);
							} else if (data?.session) {
								console.log('✅ Session created via direct code extraction');
								return;
							}
						} catch (e) {
							console.error('❌ Exception during direct code exchange:', e);
						}
					}
				}
				return;
			}
			
			if (!params) {
				// If URL has code= but parser returned null, try direct extraction
				if (url.includes('code=')) {
					const codeMatch = url.match(/[?&#]code=([^&#]+)/);
					if (codeMatch) {
						const code = decodeURIComponent(codeMatch[1]);
						try {
							const { data, error } = await supabase.auth.exchangeCodeForSession(code);
							if (error) {
								console.error('❌ Code exchange failed:', error.message);
							} else if (data?.session) {
								return;
							}
						} catch (e) {
							console.error('❌ Code exchange error:', e);
						}
					}
				}
				return;
			}

			try {
				switch (params.type) {
					case 'reset-password':
						if (params.token) {
							// Password reset - exchange token for session
							console.log('🔐 Processing password reset token');
							const { data, error } = await supabase.auth.verifyOtp({
								token_hash: params.token,
								type: 'recovery',
							});
							
							if (error) {
								console.error('❌ Password reset error:', error);
								// Error will be shown via auth state change
							} else {
								console.log('✅ Password reset successful');
								onHandled?.();
							}
						}
						break;
						
					case 'confirm-email':
						if (params.token) {
							// Email confirmation - exchange token for session
							console.log('📧 Processing email confirmation token');
							const { data, error } = await supabase.auth.verifyOtp({
								token_hash: params.token,
								type: 'email',
							});
							
							if (error) {
								console.error('❌ Email confirmation error:', error);
								// Error will be shown via auth state change
							} else {
								console.log('✅ Email confirmed successfully');
								onHandled?.();
							}
						}
						break;
						
					case 'oauth-callback':
						// OAuth callback from browser redirect
						console.log('✅ OAuth callback received');
						console.log('📋 Callback URL:', url);
						console.log('📋 Parsed params:', {
							hasToken: !!params.token,
							hasAccessToken: !!params.access_token,
							hasError: !!params.error,
							tokenLength: params.token?.length || 0,
						});
						
						// Handle errors first
						if (params.error) {
							console.error('❌ OAuth error in callback:', params.error);
							Alert.alert(
								'Sign-In Failed', 
								`An error occurred during Google sign-in: ${params.error}. Please try again.`
							);
							return;
						}
						
						// Extract OAuth code - prioritize parsed token over direct extraction
						let code = params.token || params.access_token;
						
						// Fallback: Try to extract code directly from URL if not in parsed params
						if (!code) {
							console.log('⚠️ Code not in parsed params, attempting direct URL extraction...');
							const codeMatch = url.match(/[?&#]code=([^&#]+)/);
							const codeHashMatch = url.match(/#code=([^&#]+)/);
							
							code = codeMatch ? decodeURIComponent(codeMatch[1]) : 
							       codeHashMatch ? decodeURIComponent(codeHashMatch[1]) : undefined;
							
							if (code) {
								console.log('✅ Code extracted directly from URL');
							}
						}
						
						// Exchange code for session
						if (code) {
							console.log('📝 Exchanging OAuth code for session...');
							console.log('🔑 Code length:', code.length);
							console.log('🔑 Code preview:', code.substring(0, 20) + '...');
							
							try {
								const { data, error } = await supabase.auth.exchangeCodeForSession(code);
								
								if (error) {
									console.error('❌ Code exchange error:', error);
									console.error('❌ Error details:', {
										message: error.message,
										status: error.status,
									});
									
									// Provide user-friendly error message
									let errorMessage = 'Failed to complete sign-in. Please try again.';
									if (error.message.includes('expired')) {
										errorMessage = 'The sign-in request has expired. Please try again.';
									} else if (error.message.includes('invalid')) {
										errorMessage = 'Invalid authentication code. Please try signing in again.';
									} else if (error.message) {
										errorMessage = error.message;
									}
									
									Alert.alert('Sign-In Failed', errorMessage);
									return;
								}
								
								if (data?.session) {
									console.log('✅ Session created successfully');
									console.log('✅ User ID:', data.session.user.id);
									console.log('✅ User email:', data.session.user.email);
									// onAuthStateChange will handle user state update
								} else {
									console.warn('⚠️ Code exchange returned no session');
									// Fall through to session check below
								}
							} catch (exchangeError: any) {
								console.error('❌ Exception during code exchange:', exchangeError);
								Alert.alert(
									'Sign-In Failed', 
									exchangeError.message || 'An unexpected error occurred. Please try again.'
								);
								return;
							}
						}
						
						// Fallback: Check if session was already created (Supabase might have handled it)
						if (!code) {
							console.warn('⚠️ No code found in callback URL');
							console.log('🔍 Attempting to retrieve existing session...');
							
							try {
								const { data: { session }, error: sessionError } = await supabase.auth.getSession();
								
								if (sessionError) {
									console.error('❌ Error getting session:', sessionError);
								}
								
								if (session) {
									console.log('✅ Session found after OAuth');
									console.log('✅ User ID:', session.user.id);
									console.log('✅ User email:', session.user.email);
								} else {
									console.error('❌ No code and no session found');
									Alert.alert(
										'Sign-In Failed', 
										'No authentication code received. Please try signing in again.'
									);
									return;
								}
							} catch (sessionError: any) {
								console.error('❌ Exception checking session:', sessionError);
								Alert.alert(
									'Sign-In Failed', 
									'Unable to verify sign-in status. Please try again.'
								);
								return;
							}
						}
						
						// Call handler to notify that deep link was processed
						onHandled?.();
						break;
						
					default:
						console.log('⚠️ Unknown deep link type');
				}
			} catch (error) {
				console.error('❌ Error handling deep link:', error);
			}
		};

		// Get initial URL (if app was opened via deep link)
		// This is critical for catching OAuth redirects that happen when app is in background
		Linking.getInitialURL()
			.then((url) => {
				if (url) {
					console.log('🔗 Initial URL on app start:', url);
					handleDeepLink(url);
				} else {
					console.log('🔗 No initial URL on app start');
				}
			})
			.catch((error) => {
				console.error('❌ Error getting initial URL:', error);
			});

		// Listen for deep links while app is running
		// This handles all URL schemes including exp://, shootrz://, etc.
		// CRITICAL: This must catch OAuth redirects even if connection fails
		const subscription = Linking.addEventListener('url', (event) => {
			console.log('🔗 Deep link event received via listener:', event.url);
			console.log('🔗 Deep link type:', event.url.startsWith('exp://') ? 'expo' : event.url.startsWith('shootrz://') ? 'production' : event.url.startsWith('https://') ? 'https' : 'other');
			handleDeepLink(event.url);
		});

		// Also poll for URL changes as a fallback
		// Sometimes the event listener doesn't fire if connection fails
		// This is a workaround for Expo's deep link handling
		if (__DEV__) {
			const pollInterval = setInterval(async () => {
				try {
					const currentUrl = await Linking.getInitialURL();
					if (currentUrl && currentUrl.includes('code=')) {
						console.log('🔗 Found OAuth code in URL via polling:', currentUrl);
						handleDeepLink(currentUrl);
					}
				} catch (error) {
					// Silently ignore polling errors
				}
			}, 1000); // Poll every second for OAuth callbacks
			
			// Clean up polling after 30 seconds (OAuth should complete by then)
			setTimeout(() => {
				clearInterval(pollInterval);
			}, 30000);
			
			return () => {
				subscription.remove();
				clearInterval(pollInterval);
			};
		} else {
			return () => {
				subscription.remove();
			};
		}
	}, [onHandled]);
}

