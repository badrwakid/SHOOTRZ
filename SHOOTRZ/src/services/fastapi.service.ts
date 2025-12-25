// Get API URL from environment or use defaults
// For physical devices, set EXPO_PUBLIC_API_URL=http://YOUR_IP:8000 in .env
const getApiBaseUrl = () => {
	if (process.env.EXPO_PUBLIC_API_URL) {
		return process.env.EXPO_PUBLIC_API_URL;
	}
	
	if (__DEV__) {
		// Default for iOS Simulator / Android Emulator
		// For physical devices, you'll need to set EXPO_PUBLIC_API_URL
		return 'http://127.0.0.1:8000';
	}
	
	return 'https://api.shootrz.com'; // Production
};

const BASE_URL = getApiBaseUrl();

// Log the API URL in development for debugging
if (__DEV__) {
	console.log(`🔗 FastAPI Service Base URL: ${BASE_URL}`);
	console.log(`🔗 Environment variable EXPO_PUBLIC_API_URL: ${process.env.EXPO_PUBLIC_API_URL || 'NOT SET'}`);
}


export async function getHistory(userId: string) {
  const res = await fetch(`${BASE_URL}/history/${userId}`)
  if (!res.ok) throw new Error(`history failed: ${res.status}`)
  return res.json()
}

export async function checkHealth(): Promise<boolean> {
  try {
    const healthUrl = `${BASE_URL}/health`;
    if (__DEV__) {
      console.log(`🏥 FastAPI Health check: GET ${healthUrl}`);
    }
    
    const res = await fetch(healthUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!res.ok) {
      // Only log server errors (4xx/5xx), not network errors
      if (__DEV__ && res.status >= 500) {
        console.warn(`⚠️ Health check failed (server error): ${res.status} ${res.statusText}`);
      }
      return false;
    }
    
    const data = await res.json();
    if (__DEV__) {
      console.log(`✅ Health check response:`, data);
    }
    
    return data.status === 'healthy';
  } catch (error: any) {
    // Suppress network errors - they're expected if backend is unavailable
    const isNetworkError = 
      error?.message?.includes('Network request failed') ||
      error?.message?.includes('Network Error') ||
      error?.message?.includes('Failed to fetch') ||
      error?.name === 'TypeError';
    
    // Only log non-network errors
    if (!isNetworkError && __DEV__) {
      console.warn('⚠️ Health check failed (unexpected error):', {
        message: error?.message,
        name: error?.name,
      });
    }
    
    return false;
  }
}



