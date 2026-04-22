/**
 * Canonical FastAPI paths relative to API root (see normalizeApiBaseUrl — no trailing /api on base).
 * Single place to avoid drift between client and OpenAPI.
 */
export const API_PATHS = {
	userAnalysisHistory: '/api/user/analysis-history',
	analysisComplete: '/api/analysis/complete',
	userAccount: '/api/user/account',
	userProfile: '/api/user/profile',
	userStats: '/api/user/stats',
	userStreak: '/api/user/streak',
	sessions: '/api/sessions',
	sessionDetail: (sessionId: string) => `/api/sessions/${sessionId}`,
	mvpAnalyze: '/mvp/analyze',
	mvpResult: (jobId: string) => `/mvp/result/${jobId}`,
	/** Legacy unauthenticated history (videos); prefer userAnalysisHistory */
	historyLegacy: (userId: string) => `/history/${userId}`,
	historyLegacyStats: (userId: string) => `/history/${userId}/stats`,
} as const
