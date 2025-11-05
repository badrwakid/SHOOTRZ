// Deep link utilities for handling app navigation from external links
// Supports: password reset, email confirmation, OAuth callbacks

export interface DeepLinkParams {
	type: 'reset-password' | 'confirm-email' | 'oauth-callback';
	token?: string;
	access_token?: string;
	refresh_token?: string;
	error?: string;
}

/**
 * Parse deep link URL and extract parameters
 * Examples:
 *   shootrz://reset-password?token=abc123
 *   shootrz://confirm-email?token=abc123
 *   shootrz://auth/callback?access_token=...&refresh_token=...
 */
export function parseDeepLink(url: string): DeepLinkParams | null {
	try {
		// Handle different URL formats
		let urlString = url;
		
		// Handle exp:// URLs (Expo development URLs)
		// Format: exp://192.168.56.1:8081/--/auth/callback?code=...
		// OR: exp://localhost:8081?code=... (Supabase sometimes redirects to localhost with no path)
		if (url.startsWith('exp://')) {
			// Extract query string - this is the most reliable way
			// Look for ? followed by query params
			const queryIndex = url.indexOf('?');
			if (queryIndex !== -1) {
				// Extract everything after ? as query string
				const queryPart = url.substring(queryIndex);
				// Also try to get path if it exists
				const pathMatch = url.match(/exp:\/\/[^?]+\/([^?]+)/);
				if (pathMatch) {
					// Has path + query
					urlString = '/' + pathMatch[1] + queryPart;
				} else {
					// No path, just query (e.g., exp://localhost:8081?code=...)
					urlString = queryPart;
				}
			} else {
				// No query, try to extract path
				const pathMatch = url.match(/exp:\/\/[^/]+(\/.*)$/);
				if (pathMatch) {
					urlString = pathMatch[1];
				}
			}
		}
		// Handle regular URLs (shootrz://, https://, etc.)
		else if (url.includes('://')) {
			try {
				const urlObj = new URL(url);
				urlString = urlObj.pathname + urlObj.search;
			} catch (e) {
				// If URL constructor fails, try to extract path manually
				const match = url.match(/[^:]+:\/\/[^/]+(\/.*)$/);
				if (match) {
					urlString = match[1];
				}
			}
		}
		
		// Parse shootrz://reset-password?token=...
		if (urlString.includes('reset-password')) {
			const tokenMatch = urlString.match(/[?&]token=([^&]+)/);
			return {
				type: 'reset-password',
				token: tokenMatch ? decodeURIComponent(tokenMatch[1]) : undefined,
			};
		}
		
		// Parse shootrz://confirm-email?token=...
		if (urlString.includes('confirm-email')) {
			const tokenMatch = urlString.match(/[?&]token=([^&]+)/);
			return {
				type: 'confirm-email',
				token: tokenMatch ? decodeURIComponent(tokenMatch[1]) : undefined,
			};
		}
		
		// Parse OAuth callback URLs
		// Handles multiple formats:
		// - exp://192.168.56.1:8081/--/auth/callback?code=...
		// - exp://localhost:8081?code=... (Supabase sometimes redirects to localhost)
		// - shootrz://auth/callback?code=...
		// - https://...supabase.co/auth/v1/callback?code=...
		
		// CRITICAL: Check for code parameter first - this is the most reliable indicator
		// Even if URL format looks wrong (like exp://localhost), if it has code=, it's an OAuth callback
		const hasCode = url.includes('code=') || urlString.includes('code=');
		
		// Also check for callback paths
		const isAuthCallback = url.includes('auth/callback') || 
		                       urlString.includes('auth/callback') || 
		                       urlString.includes('oauth-callback') || 
		                       urlString.includes('/auth/v1/callback');
		
		// If URL has code parameter OR callback path, it's an OAuth callback
		if (hasCode || isAuthCallback) {
			// Extract code from URL - try multiple patterns
			// Pattern 1: Query parameter: ?code=xxx or &code=xxx
			let codeMatch = url.match(/[?&]code=([^&#]+)/) || urlString.match(/[?&]code=([^&#]+)/);
			// Pattern 2: Fragment: #code=xxx
			if (!codeMatch) {
				codeMatch = url.match(/#code=([^&#]+)/) || urlString.match(/#code=([^&#]+)/);
			}
			// Pattern 3: Hash fragment after ?: ?xxx#code=xxx
			if (!codeMatch) {
				codeMatch = url.match(/[&#]code=([^&#]+)/) || urlString.match(/[&#]code=([^&#]+)/);
			}
			
			// Extract error parameter
			const errorMatch = url.match(/[?&#]error=([^&#]+)/) || urlString.match(/[?&#]error=([^&#]+)/);
			
			// Extract access_token and refresh_token if present
			const accessTokenMatch = url.match(/[?&#]access_token=([^&#]+)/) || urlString.match(/[?&#]access_token=([^&#]+)/);
			const refreshTokenMatch = url.match(/[?&#]refresh_token=([^&#]+)/) || urlString.match(/[?&#]refresh_token=([^&#]+)/);
			
			return {
				type: 'oauth-callback',
				token: codeMatch ? decodeURIComponent(codeMatch[1]) : undefined,
				access_token: accessTokenMatch ? decodeURIComponent(accessTokenMatch[1]) : undefined,
				refresh_token: refreshTokenMatch ? decodeURIComponent(refreshTokenMatch[1]) : undefined,
				error: errorMatch ? decodeURIComponent(errorMatch[1]) : undefined,
			};
		}
		
		return null;
	} catch (error) {
		console.error('Error parsing deep link:', error);
		return null;
	}
}

/**
 * Build deep link URL for password reset
 */
export function buildResetPasswordLink(token: string): string {
	return `shootrz://reset-password?token=${encodeURIComponent(token)}`;
}

/**
 * Build deep link URL for email confirmation
 */
export function buildConfirmEmailLink(token: string): string {
	return `shootrz://confirm-email?token=${encodeURIComponent(token)}`;
}

/**
 * Build deep link URL for OAuth callback
 */
export function buildOAuthCallbackLink(params: {
	access_token?: string;
	refresh_token?: string;
	error?: string;
}): string {
	const query = new URLSearchParams();
	if (params.access_token) query.append('access_token', params.access_token);
	if (params.refresh_token) query.append('refresh_token', params.refresh_token);
	if (params.error) query.append('error', params.error);
	
	return `shootrz://auth/callback?${query.toString()}`;
}

