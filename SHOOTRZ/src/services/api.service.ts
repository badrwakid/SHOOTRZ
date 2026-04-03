import axios, { AxiosResponse } from 'axios';
import type {
	HealthResponse as ApiHealthResponse,
	HistoryResponse,
	HistoryStatsResponse,
	MVPResultResponse as ApiMVPResultResponse,
} from '../types/contracts';

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

export const API_BASE_URL = getApiBaseUrl();

export interface AnalysisResponse {
  success: boolean;
  video_id: string;

  // Basic metrics with confidence
  metrics: {
    elbow_angle: number;
    elbow_confidence: number;
    knee_angle: number;
    knee_confidence: number;
    release_angle: number;
    release_confidence: number;
    body_alignment: number;
    alignment_confidence: number;
  };

  // Advanced metrics
  advanced_metrics: {
    follow_through_angle: number;
    shot_arc: number;
    release_height: number;
    jump_timing: number;
    consistency_score: number;
    body_sway: number;
  };

  // Enhanced scores
  scores: {
    elbow: number;
    balance: number;
    release: number;
    alignment: number;
    follow_through: number;
    consistency: number;
    total: number;
  };

  // Professional comparison
  professional_comparison: {
    best_match: {
      name: string;
      similarity: number;
      position: string;
      style: string;
      best_for: string;
      key_differences: Array<{
        metric: string;
        user_value: number;
        player_value: number;
        difference: number;
        improvement_direction: string;
      }>;
    };
    top_matches: Array<{
      name: string;
      similarity: number;
      position: string;
      style: string;
      key_differences: string[];
    }>;
    improvement_path: Array<{
      metric: string;
      current: number;
      target: number;
      impact: string;
      drill: string;
    }>;
  };

  // Phase analysis
  phases: {
    setup: PhaseData;
    dip: PhaseData;
    release: PhaseData;
    follow_through: PhaseData;
  };

  // Enhanced feedback
  tips: string[];
  biomechanics_insights: string[];
  injury_prevention: string[];
  drill_recommendations: Array<{
    name: string;
    description: string;
    sets: string;
    focus: string;
  }>;

  // Performance predictions
  predicted_make_rate: number;

  // Frame data for graphs
  frame_data: {
    frame_number: number;
    elbow_angle: number;
    knee_angle: number;
    release_angle: number;
    body_alignment: number;
  }[];

  timestamp: string;
  processing_stats: {
    processing_time: number;
    total_frames: number;
    processed_frames: number;
    pose_detection_rate: number;
    processing_fps: number;
  };

  // Performance level
  performance_level?: string;
}

export interface PhaseData {
  start_frame: number;
  end_frame: number;
  duration: number;
  metrics: {
    elbow_angle: number;
    knee_angle: number;
    release_angle: number;
    body_alignment: number;
  };
  score: number;
  feedback: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  uptime: number;
}

export interface MVPMetric {
	name: string
	value: number
	unit: string
	verdict: 'Good' | 'Needs Work' | 'Low Confidence'
	explanation: string
	confidence: number
	frame_range?: [number, number]
}

export interface MVPScoreComponent {
	name: string
	value: number
	unit: string
	weight: number
	explanation: string
}

export interface MVPResultResponse {
	status: 'queued' | 'processing' | 'completed' | 'failed'
	contract_version?: string
	run_id?: string
	overall_score?: number
	feedback_summary?: string
	feedback_bullets?: string[]
	metrics?: MVPMetric[]
	score_components?: MVPScoreComponent[]
	shot_window?: {
		start_frame?: number
		crouch_frame?: number
		release_frame?: number
		end_frame?: number
		confidence?: string
		confidence_score?: number
	}
	events?: {
		start?: MVPEvent
		crouch?: MVPEvent
		release?: MVPEvent
		end?: MVPEvent
	}
	angles_data?: {
		frames: number[]
		timestamps: number[]
		elbow: Array<number | null>
		knee: Array<number | null>
		wrist: Array<number | null>
	}
	artifacts?: {
		overlay_video?: string | null
		angles_csv?: string
		report_json?: string
		event_candidates?: string
		event_confidence?: string
		feature_table?: string
		signals_smoothed?: string
		warnings?: string
	}
	key_frame_images?: {
		start?: string
		crouch?: string
		release?: string
		end?: string
	}
	diagnostics?: Record<string, unknown>
	quality_warnings?: string[]
	error?: string
	error_detail?: string
}

export interface MVPEvent {
	frame?: number | null
	timestamp?: number | null
	status?: 'detected' | 'estimated' | 'missing' | string
	confidence?: number
	reason_codes?: string[]
	alternatives?: Array<{
		frame_id: number
		score: number
		kind: string
	}>
}

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
    this.baseURL = API_BASE_URL;
    this.timeout = 120000; // 2 minutes timeout for video processing
    
    // Log the API URL in development for debugging
    if (__DEV__) {
      console.log(`🔗 API Base URL: ${this.baseURL}`);
      console.log(`🔗 Environment variable EXPO_PUBLIC_API_URL: ${process.env.EXPO_PUBLIC_API_URL || 'NOT SET'}`);
    }
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
      const requestUrl = `${this.baseURL}/mvp/analyze`;
      
      formData.append('file', {
        uri: videoUri,
        type: 'video/mp4',
        name: filename,
      } as any);

      if (__DEV__) {
        console.log('📹 MVP Analysis - Uploading video:', { filename, shootingSide });
      }

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

        if (__DEV__) {
          console.log('✅ MVP Analysis queued:', response.data);
        }

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
      const response = await axios.get(`${this.baseURL}/mvp/result/${jobId}`, {
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
      if (__DEV__) {
        console.log(`🏥 Health check: GET ${healthUrl}`);
      }
      
      const response: AxiosResponse<ApiHealthResponse> = await axios.get(healthUrl, {
        timeout: 5000,
        validateStatus: (status) => status < 500, // Don't throw on 404, just return false
      });

      if (__DEV__) {
        console.log(`✅ Health check response: ${response.status}`, response.data);
      }
      
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
   * Get user's analysis history
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
        `${this.baseURL}/history/${userId}?${params.toString()}`,
        { timeout: this.timeout }
      )
      return response.data
    } catch (error: any) {
      console.error('Error fetching history:', error)
      throw new Error(error.response?.data?.detail || 'Failed to fetch history')
    }
  }

  /**
   * Get history statistics
   */
  async getHistoryStats(userId: string): Promise<HistoryStatsResponse> {
    try {
      const response = await axios.get(
        `${this.baseURL}/history/${userId}/stats`,
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
}

// Export singleton instance
export const apiService = new ApiService();