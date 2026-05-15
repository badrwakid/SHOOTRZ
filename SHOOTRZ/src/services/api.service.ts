import axios, { AxiosResponse } from 'axios';
import { supabase } from './supabase.client'
// BUG FIX: Import canonical types from contracts.ts instead of duplicating them locally
import type {
	HealthResponse as ApiHealthResponse,
	HistoryResponse,
	HistoryStatsResponse,
	MVPResultResponse as ApiMVPResultResponse,
	MVPMetric as ApiMVPMetric,
	MVPScoreComponent as ApiMVPScoreComponent,
	MVPEvent as ApiMVPEvent,
	UserProfile,
	UserStats,
	UserStreak,
	DrillCompletion,
	WorkoutProgress,
	ChatHistoryMessage,
	UserExportResponse,
	UserPreferencesPayload,
	UserProfileResponse,
} from '../types/contracts';
import { API_PATHS } from '../constants/apiEndpoints';

// FastAPI Backend (port 8000)
// - iOS Simulator: Use 'http://127.0.0.1:8000' or 'http://localhost:8000'
// - Android Emulator: Use 'http://10.0.2.2:8000'
// - Physical Device: Use your computer's IP (e.g., 'http://192.168.1.4:8000')
//   To find your IP: Windows: ipconfig | Mac/Linux: ifconfig

// FastAPI Backend (port 8000)
// For iOS Simulator: Use 'http://127.0.0.1:8000' or 'http://localhost:8000'
// For Android Emulator: Use 'http://10.0.2.2:8000'
// For Physical Device: Use your computer's IP (e.g., 'http://192.168.1.4:8000')
//   To find your IP: Windows: ipconfig | Mac/Linux: ifconfig

/**
 * Root URL of the FastAPI app (no trailing slash, no trailing /api).
 * Paths in this file already include `/api/...` where needed; a common mistake is
 * setting EXPO_PUBLIC_API_URL to `http://host:8000/api`, which would produce
 * `/api/api/user/...` and 404 on Progress, complete, and delete account.
 */
export function normalizeApiBaseUrl(url: string): string {
	let u = url.trim().replace(/\/+$/, '')
	if (u.endsWith('/api')) {
		u = u.slice(0, -4).replace(/\/+$/, '')
	}
	return u
}

// Get API URL from environment or use defaults
// For physical devices, set EXPO_PUBLIC_API_URL=http://YOUR_IP:8000 in .env
const getApiBaseUrl = () => {
	if (process.env.EXPO_PUBLIC_API_URL) {
		return normalizeApiBaseUrl(process.env.EXPO_PUBLIC_API_URL)
	}

	if (__DEV__) {
		// Default for iOS Simulator / Android Emulator
		// For physical devices, you'll need to set EXPO_PUBLIC_API_URL
		return 'http://127.0.0.1:8000'
	}

	return 'https://api.shootrz.com' // Production
}

export const API_BASE_URL = getApiBaseUrl()

/** Log legacy fallback warning at most once (prefetch + screens call history often). */
let warnedAnalysisHistory404 = false

/** In __DEV__, log resolved base URL once on first authenticated API use (debugging 404s). */
let loggedApiBaseDevOnce = false



// BUG FIX: Duplicate HealthResponse, MVPMetric, MVPScoreComponent, MVPResultResponse, MVPEvent
// removed — now imported from contracts.ts (single source of truth)
export type HealthResponse = ApiHealthResponse
export type MVPMetric = ApiMVPMetric
export type MVPScoreComponent = ApiMVPScoreComponent
export type MVPResultResponse = ApiMVPResultResponse
export type MVPEvent = ApiMVPEvent

export interface PerformanceResponse {
  success: boolean;
  summary: {
    total_evaluations: number;
    average_processing_time: number;
    average_fps: number;
    average_pose_detection_rate: number;
    average_accuracy: number;
    total_videos_processed: number;
    successful_analyses: number;
    failed_analyses: number;
  };
  trends: any;
  timestamp: string;
}

export interface SystemStatusResponse {
  success: boolean;
  system_status: {
    upload_folder: string;
    processed_folder: string;
    max_video_length: number;
    max_file_size_mb: number;
    allowed_extensions: string[];
  };
  privacy_status: {
    total_pending: number;
    pending_deletions: any[];
    retention_days: number;
    cleanup_thread_running: boolean;
  };
  timestamp: string;
}

class ApiService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = normalizeApiBaseUrl(API_BASE_URL)
    this.timeout = 120000; // 2 minutes timeout for video processing
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    let { data } = await supabase.auth.getSession()
    let token = data?.session?.access_token
    if (!token) {
      const refreshed = await supabase.auth.refreshSession()
      token = refreshed.data?.session?.access_token
    }
    if (!token) {
      return {}
    }
    return { Authorization: `Bearer ${token}` }
  }

  private logResolvedBaseOnce(label: string): void {
    if (!__DEV__ || loggedApiBaseDevOnce) {
      return
    }
    loggedApiBaseDevOnce = true
    console.log(`[api] resolved base ${this.baseURL} (first call: ${label})`)
  }

  /**
   * MVP Analysis - Analyze video with deterministic pipeline
   */
  async analyzeMVP(videoUri: string, shootingSide: string = 'auto'): Promise<{ job_id: string; status: string }> {
    try {
      if (!videoUri || videoUri.trim() === '') {
        throw new Error('Invalid video URI: URI is empty');
      }

      const formData = new FormData();
      const filename = this.getVideoFilename(videoUri);
      const requestUrl = `${this.baseURL}${API_PATHS.mvpAnalyze}`;
      
      formData.append('file', {
        uri: videoUri,
        type: 'video/mp4',
        name: filename,
      } as any);

      let response;
      try {
        response = await axios.post(
          requestUrl,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            params: {
              shooting_side: shootingSide
            },
            timeout: this.timeout,
          }
        );

        return { job_id: response.data.job_id, status: response.data.status };
      } catch (axiosError: any) {
        throw axiosError;
      }
    } catch (error: any) {

      if (__DEV__) {
        console.error('❌ MVP Analysis error:', error?.response?.data || error?.message);
      }

      if (error.response) {
        throw new Error(`Upload failed: ${error.response.data?.detail || 'Unknown error'}`);
      } else if (error.request) {
        throw new Error('Network error: Could not reach server.');
      } else {
        throw new Error(error.message || 'Upload failed');
      }
    }
  }

  /**
   * Get MVP analysis result
   */
  async getMVPResult(jobId: string): Promise<ApiMVPResultResponse> {
    try {
      const response = await axios.get(`${this.baseURL}${API_PATHS.mvpResult(jobId)}`, {
        timeout: 30000,
      });
      return response.data;
    } catch (error: any) {
      console.error('Error getting MVP result:', error);
      throw error;
    }
  }

  /**
   * Helper to extract filename from URI
   */
  private getVideoFilename(uri: string): string {
    try {
      const parts = uri.split('/');
      let filename = parts[parts.length - 1];
      if (filename.includes('?')) {
        filename = filename.split('?')[0];
      }
      if (filename.endsWith('.mp4') || filename.endsWith('.mov') || filename.endsWith('.m4v')) {
        return filename;
      }
      return 'shot.mp4';
    } catch (error) {
      return 'shot.mp4';
    }
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const healthUrl = `${this.baseURL}/health`;
      
      const response: AxiosResponse<ApiHealthResponse> = await axios.get(healthUrl, {
        timeout: 5000,
        validateStatus: (status) => status < 500, // Don't throw on 404, just return false
      });

      return response.status === 200 && response.data?.status === 'healthy';
    } catch (error: any) {
      // Suppress network errors - they're expected if backend is unavailable
      // Only log server errors (5xx) or unexpected errors
      const isNetworkError = 
        error?.code === 'ECONNABORTED' || 
        error?.code === 'ERR_NETWORK' ||
        error?.message?.includes('Network request failed') ||
        error?.message?.includes('Network Error') ||
        !error?.response; // No response means network error
      
      if (!isNetworkError && __DEV__) {
        // Log server errors or unexpected errors
        console.warn('⚠️ Health check failed (server error):', {
          status: error?.response?.status,
          message: error?.message,
        });
      }
      
      return false;
    }
  }


  /**
   * Get detailed health information
   */
  async getHealthInfo(): Promise<ApiHealthResponse | null> {
    try {
      const response: AxiosResponse<ApiHealthResponse> = await axios.get(`${this.baseURL}/health`, {
        timeout: 5000,
      });

      return response.data;
    } catch (error) {
      console.error('Error getting health info:', error);
      return null;
    }
  }

  /**
   * Get performance metrics
   */
  // Legacy endpoints - not implemented in FastAPI yet
  async getPerformanceMetrics(): Promise<PerformanceResponse | null> {
    console.warn('getPerformanceMetrics not implemented in FastAPI yet')
    return null
  }

  async getSystemStatus(): Promise<SystemStatusResponse | null> {
    console.warn('getSystemStatus not implemented in FastAPI yet')
    return null
  }

  async forceCleanup(): Promise<boolean> {
    console.warn('forceCleanup not implemented in FastAPI yet')
    return false
  }

  /**
   * Test API connection
   */
  async testConnection(): Promise<{ success: boolean; message: string }> {
    try {
      const healthInfo = await this.getHealthInfo();

      if (healthInfo) {
        return {
          success: true,
          message: `API is healthy. Version: ${healthInfo.version}`,
        };
      } else {
        return {
          success: false,
          message: 'API health check failed',
        };
      }
    } catch (error: any) {
      return {
        success: false,
        message: `Connection failed: ${error.message}`,
      };
    }
  }


  /**
   * Get API configuration
   */
  getConfig() {
    return {
      baseURL: this.baseURL,
      timeout: this.timeout,
      isDevelopment: __DEV__,
    };
  }

  /**
   * Authenticated analysis history (MVP summaries + metrics). Preferred.
   *
   * If the app points at a server that has not been updated with the
   * authenticated history route, the client may get HTTP 404. We then fall back
   * to the legacy unauthenticated path for the current Supabase user id so
   * development does not go blank. Production should expose the primary route;
   * the fallback is a best-effort read of video rows, not a full analysis summary.
   */
  async getAnalysisHistory(
    limit: number = 100,
    offset: number = 0,
  ): Promise<HistoryResponse> {
    const headers = await this.getAuthHeaders()
    if (!headers.Authorization) {
      throw new Error('Not authenticated')
    }
    this.logResolvedBaseOnce(`GET ${API_PATHS.userAnalysisHistory}`)
    const params = new URLSearchParams()
    params.append('limit', String(limit))
    params.append('offset', String(offset))
    const url = `${this.baseURL}${API_PATHS.userAnalysisHistory}?${params.toString()}`
    try {
      const response = await axios.get(url, { headers, timeout: this.timeout })
      return response.data
    } catch (err: any) {
      const status = err.response?.status
      if (status === 404) {
        const { data: userData } = await supabase.auth.getUser()
        const uid = userData.user?.id
        if (uid) {
          if (__DEV__ && !warnedAnalysisHistory404) {
            warnedAnalysisHistory404 = true
            console.warn(
              `[api] ${this.baseURL} returned 404 for ${API_PATHS.userAnalysisHistory}. ` +
                'The process on this host:port is missing that route (restart uvicorn from this repo). ' +
                `Confirm GET ${this.baseURL}/health → has_analysis_history_route: true. ` +
                `Using legacy GET ${API_PATHS.historyLegacy('<user_id>')} until fixed.`,
            )
          }
          return this.getHistory(uid, limit, offset)
        }
      }
      throw new Error(
        err.response?.data?.detail || err.message || 'Failed to fetch analysis history',
      )
    }
  }

  /**
   * Legacy unauthenticated history (videos only). Avoid for logged-in users.
   */
  async getHistory(
    userId: string,
    limit?: number,
    offset?: number
  ): Promise<HistoryResponse> {
    try {
      const params = new URLSearchParams()
      if (limit) params.append('limit', limit.toString())
      if (offset) params.append('offset', offset.toString())
      
      const response = await axios.get(
        `${this.baseURL}${API_PATHS.historyLegacy(userId)}?${params.toString()}`,
        { timeout: this.timeout }
      )
      return response.data
    } catch (error: any) {
      console.error('Error fetching history:', error)
      throw new Error(error.response?.data?.detail || 'Failed to fetch history')
    }
  }

  /**
   * Persist a completed MVP job to Supabase for the current user.
   */
  async completeMVPAnalysis(jobId: string): Promise<{
    success: boolean
    session_id?: string | null
    video_id?: string | null
    already_persisted?: boolean
  }> {
    const headers = await this.getAuthHeaders()
    if (!headers.Authorization) {
      throw new Error('Not authenticated')
    }
    const attempt = async () =>
      axios.post(
        `${this.baseURL}${API_PATHS.analysisComplete}`,
        { job_id: jobId },
        { headers, timeout: 60000 },
      )
    try {
      const response = await attempt()
      return response.data
    } catch (first: any) {
      if (first.response?.status === 401) {
        await supabase.auth.refreshSession()
        const retryAuth = await attempt()
        return retryAuth.data
      }
      if (first.response?.status === 404) {
        throw new Error(
          'Could not reach POST /api/analysis/complete (404). Set EXPO_PUBLIC_API_URL to your API ' +
            'host only (e.g. http://192.168.x.x:8000) with no trailing /api, restart Expo and the backend.',
        )
      }
      if (first.response?.status >= 500 || first.code === 'ECONNABORTED') {
        const retry = await attempt()
        return retry.data
      }
      throw new Error(first.response?.data?.detail || first.message || 'Failed to save analysis')
    }
  }

  /**
   * Delete all server-side user data and the Auth user (requires Bearer token).
   */
  async deleteAccount(): Promise<{ status: string; user_id?: string }> {
    const headers = await this.getAuthHeaders()
    if (!headers.Authorization) {
      throw new Error('Not authenticated')
    }
    try {
      const response = await axios.delete(`${this.baseURL}${API_PATHS.userAccount}`, {
        headers,
        timeout: 60000,
      })
      return response.data
    } catch (err: any) {
      if (err.response?.status === 401) {
        await supabase.auth.refreshSession()
        const response = await axios.delete(`${this.baseURL}${API_PATHS.userAccount}`, {
          headers: await this.getAuthHeaders(),
          timeout: 60000,
        })
        return response.data
      }
      if (err.response?.status === 404) {
        throw new Error(
          'Delete account endpoint not found. Use EXPO_PUBLIC_API_URL without a trailing /api ' +
            `(current base: ${this.baseURL}), and restart the FastAPI server with the latest code.`,
        )
      }
      throw new Error(err.response?.data?.detail || err.message || 'Failed to delete account')
    }
  }

  /**
   * Get history statistics
   */
  async getHistoryStats(userId: string): Promise<HistoryStatsResponse> {
    try {
      const response = await axios.get(
        `${this.baseURL}${API_PATHS.historyLegacyStats(userId)}`,
        { timeout: this.timeout }
      )
      return response.data
    } catch (error: any) {
      console.error('Error fetching history stats:', error)
      throw new Error(error.response?.data?.detail || 'Failed to fetch stats')
    }
  }

  /**
   * Create a practice session
   */
  async createSession(userId: string, title?: string, date?: string): Promise<any> {
    try {
      const response = await axios.post(
        `${this.baseURL}/sessions/${userId}`,
        { title, date },
        { timeout: this.timeout }
      )
      return response.data
    } catch (error: any) {
      console.error('Error creating session:', error)
      throw new Error(error.response?.data?.detail || 'Failed to create session')
    }
  }

  // ---------------------------------------------------------------------------
  // New Supabase-backed endpoints (authenticated)
  // ---------------------------------------------------------------------------

  async getUserProfile(): Promise<UserProfileResponse> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}${API_PATHS.userProfile}`, {
      headers, timeout: 15000,
    })
    return response.data as UserProfileResponse
  }

  async updateUserProfile(data: Partial<UserProfile>): Promise<any> {
    const snaked: Record<string, any> = {}
    if ((data as any).name !== undefined) snaked.name = (data as any).name
    if ((data as any).username !== undefined) snaked.username = (data as any).username
    if ((data as any).skillLevel !== undefined) snaked.skill_level = (data as any).skillLevel
    if ((data as any).position !== undefined) snaked.position = (data as any).position
    if ((data as any).hasCompletedOnboarding !== undefined) {
      snaked.has_completed_onboarding = (data as any).hasCompletedOnboarding
    }
    if (data.primaryGoal !== undefined) snaked.primary_goal = data.primaryGoal
    if (data.trainingFrequency !== undefined) snaked.training_frequency = data.trainingFrequency
    if (data.preferredDrillDuration !== undefined) snaked.preferred_drill_duration = data.preferredDrillDuration
    if (data.age !== undefined) snaked.age = data.age
    if (data.heightCm !== undefined) snaked.height_cm = data.heightCm
    if (data.weightKg !== undefined) snaked.weight_kg = data.weightKg
    if (data.dominantHand !== undefined) snaked.dominant_hand = data.dominantHand
    if (data.yearsPlaying !== undefined) snaked.years_playing = data.yearsPlaying
    if (data.notificationsEnabled !== undefined) snaked.notifications_enabled = data.notificationsEnabled
    if (data.darkModeEnabled !== undefined) snaked.dark_mode_enabled = data.darkModeEnabled
    if (data.analyticsEnabled !== undefined) snaked.analytics_enabled = data.analyticsEnabled
    if (data.coachingStyle !== undefined) snaked.coaching_style = data.coachingStyle
    const request = async () => {
      const headers = await this.getAuthHeaders()
      return axios.put(`${this.baseURL}${API_PATHS.userProfile}`, snaked, {
        headers, timeout: 15000,
      })
    }
    try {
      const response = await request()
      return response.data
    } catch (err: any) {
      if (err?.response?.status === 401) {
        await supabase.auth.refreshSession()
        const retry = await request()
        return retry.data
      }
      throw err
    }
  }

  async exportUserData(): Promise<UserExportResponse> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}${API_PATHS.userExport}`, {
      headers, timeout: 120000,
    })
    return response.data as UserExportResponse
  }

  async updateUserPreferences(payload: UserPreferencesPayload): Promise<UserProfileResponse> {
    const headers = await this.getAuthHeaders()
    const response = await axios.put(`${this.baseURL}${API_PATHS.userPreferences}`, payload, {
      headers, timeout: 15000,
    })
    return response.data as UserProfileResponse
  }

  async getUserStats(): Promise<UserStats> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}${API_PATHS.userStats}`, {
      headers, timeout: 15000,
    })
    const d = response.data
    return {
      totalSessions: d.total_sessions ?? 0,
      avgScore: d.avg_score ?? undefined,
      bestScore: d.best_score ?? undefined,
      totalShots: d.total_shots ?? undefined,
      currentStreak: d.current_streak ?? 0,
      longestStreak: d.longest_streak ?? 0,
      lastSessionDate: d.last_session_date ?? undefined,
    }
  }

  async getUserStreak(): Promise<UserStreak> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}${API_PATHS.userStreak}`, {
      headers, timeout: 15000,
    })
    const d = response.data
    return {
      currentStreak: d.current_streak ?? 0,
      longestStreak: d.longest_streak ?? 0,
      lastActivityDate: d.last_activity_date ?? undefined,
    }
  }

  async getSessionsAuth(limit: number = 20, offset: number = 0): Promise<any> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}${API_PATHS.sessions}`, {
      headers, timeout: 15000,
      params: { limit, offset },
    })
    return response.data
  }

  async getSessionDetail(sessionId: string): Promise<any> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}${API_PATHS.sessionDetail(sessionId)}`, {
      headers, timeout: 15000,
    })
    return response.data
  }

  async getDrillCompletions(limit: number = 50): Promise<{ completions: DrillCompletion[]; count: number }> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}/api/drills/completions`, {
      headers, timeout: 15000,
      params: { limit },
    })
    return response.data
  }

  async completeDrill(data: {
    drillId: string; drillName: string;
    durationSeconds?: number; userRating?: number; notes?: string
  }): Promise<any> {
    const headers = await this.getAuthHeaders()
    const response = await axios.post(`${this.baseURL}/api/drills/complete`, {
      drill_id: data.drillId,
      drill_name: data.drillName,
      duration_seconds: data.durationSeconds,
      user_rating: data.userRating,
      notes: data.notes,
    }, { headers, timeout: 15000 })
    return response.data
  }

  async getWorkoutProgress(): Promise<{ workouts: WorkoutProgress[]; count: number }> {
    const headers = await this.getAuthHeaders()
    const response = await axios.get(`${this.baseURL}/api/workouts/progress`, {
      headers, timeout: 15000,
    })
    return response.data
  }

  async updateWorkoutProgress(workoutId: string, data: {
    workoutName: string; status?: string;
    drillsCompleted?: number; drillsTotal?: number;
  }): Promise<any> {
    const headers = await this.getAuthHeaders()
    const response = await axios.put(`${this.baseURL}/api/workouts/${workoutId}/progress`, {
      workout_name: data.workoutName,
      status: data.status,
      drills_completed: data.drillsCompleted,
      drills_total: data.drillsTotal,
    }, { headers, timeout: 15000 })
    return response.data
  }
}

// Export singleton instance
export const apiService = new ApiService();