import axios, { AxiosResponse } from 'axios';

// IMPORTANT: Change this based on your setup:
// - iOS Simulator: Use 'http://127.0.0.1:5000' or 'http://localhost:5000'
// - Android Emulator: Use 'http://10.0.2.2:5000'
// - Physical Device: Use your computer's IP (e.g., 'http://192.168.1.4:5000')
//   To find your IP: Windows: ipconfig | Mac/Linux: ifconfig

const API_BASE_URL = __DEV__ 
  ? 'http://192.168.1.4:5000'  // Your backend is running on this IP (from logs)
  : 'https://api.shootrz.com';  // Production (update with your domain)

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
  }

  /**
   * Analyze video for basketball shooting form with enhanced AI features
   */
  async analyzeVideo(videoUri: string): Promise<AnalysisResponse> {
    try {
      const formData = new FormData();
      
      // Append video file
      formData.append('video', {
        uri: videoUri,
        type: 'video/mp4',
        name: 'shot.mp4',
      } as any);
      
      const response: AxiosResponse<AnalysisResponse> = await axios.post(
        `${this.baseURL}/api/analyze`, 
        formData, 
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: this.timeout,
        }
      );
      
      return response.data;
    } catch (error: any) {
      console.error('Error analyzing video:', error);
      
      if (error.response) {
        // Server responded with error status
        throw new Error(error.response.data?.error || 'Analysis failed');
      } else if (error.request) {
        // Request was made but no response received
        throw new Error('Network error: Could not reach analysis server');
      } else {
        // Something else happened
        throw new Error(error.message || 'Unknown error occurred');
      }
    }
  }

  /**
   * Get annotated video URL
   */
  getAnnotatedVideoUrl(videoId: string): string {
    return `${this.baseURL}/api/video/${videoId}`;
  }

  /**
   * Get professional player comparison data
   */
  async getProfessionalComparison(userMetrics: any): Promise<any> {
    try {
      const response: AxiosResponse<any> = await axios.post(
        `${this.baseURL}/api/compare`,
        { metrics: userMetrics },
        { timeout: 30000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting professional comparison:', error);
      return null;
    }
  }

  /**
   * Get phase analysis for a specific video
   */
  async getPhaseAnalysis(videoId: string): Promise<any> {
    try {
      const response: AxiosResponse<any> = await axios.get(
        `${this.baseURL}/api/phases/${videoId}`,
        { timeout: 30000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting phase analysis:', error);
      return null;
    }
  }

  /**
   * Get frame-by-frame data for angle graphs
   */
  async getFrameData(videoId: string): Promise<any> {
    try {
      const response: AxiosResponse<any> = await axios.get(
        `${this.baseURL}/api/frames/${videoId}`,
        { timeout: 30000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting frame data:', error);
      return null;
    }
  }

  /**
   * Get advanced metrics analysis
   */
  async getAdvancedMetrics(videoId: string): Promise<any> {
    try {
      const response: AxiosResponse<any> = await axios.get(
        `${this.baseURL}/api/advanced/${videoId}`,
        { timeout: 30000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting advanced metrics:', error);
      return null;
    }
  }

  /**
   * Get improvement recommendations
   */
  async getImprovementRecommendations(userMetrics: any, professionalComparison: any): Promise<any> {
    try {
      const response: AxiosResponse<any> = await axios.post(
        `${this.baseURL}/api/improvements`,
        { 
          metrics: userMetrics,
          comparison: professionalComparison 
        },
        { timeout: 30000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting improvement recommendations:', error);
      return null;
    }
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response: AxiosResponse<HealthResponse> = await axios.get(
        `${this.baseURL}/health`,
        { timeout: 5000 }
      );
      
      return response.data.status === 'healthy';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  /**
   * Get detailed health information
   */
  async getHealthInfo(): Promise<HealthResponse | null> {
    try {
      const response: AxiosResponse<HealthResponse> = await axios.get(
        `${this.baseURL}/health`,
        { timeout: 5000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting health info:', error);
      return null;
    }
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(): Promise<PerformanceResponse | null> {
    try {
      const response: AxiosResponse<PerformanceResponse> = await axios.get(
        `${this.baseURL}/api/performance`,
        { timeout: 10000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting performance metrics:', error);
      return null;
    }
  }

  /**
   * Get system status
   */
  async getSystemStatus(): Promise<SystemStatusResponse | null> {
    try {
      const response: AxiosResponse<SystemStatusResponse> = await axios.get(
        `${this.baseURL}/api/status`,
        { timeout: 10000 }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error getting system status:', error);
      return null;
    }
  }

  /**
   * Force cleanup of old files
   */
  async forceCleanup(): Promise<boolean> {
    try {
      const response = await axios.post(
        `${this.baseURL}/api/cleanup`,
        {},
        { timeout: 30000 }
      );
      
      return response.data.success;
    } catch (error) {
      console.error('Error forcing cleanup:', error);
      return false;
    }
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
          message: `API is healthy. Version: ${healthInfo.version}`
        };
      } else {
        return {
          success: false,
          message: 'API health check failed'
        };
      }
    } catch (error: any) {
      return {
        success: false,
        message: `Connection failed: ${error.message}`
      };
    }
  }

  /**
   * Validate video file before upload
   */
  validateVideoFile(videoUri: string, duration?: number): { valid: boolean; message: string } {
    try {
      // Check if URI is valid
      if (!videoUri || videoUri.trim() === '') {
        return { valid: false, message: 'No video file selected' };
      }

      // Check duration if provided
      if (duration && duration > 30) {
        return { valid: false, message: 'Video too long. Maximum 30 seconds allowed' };
      }

      if (duration && duration < 1) {
        return { valid: false, message: 'Video too short. Minimum 1 second required' };
      }

      return { valid: true, message: 'Video file is valid' };
    } catch (error) {
      return { valid: false, message: 'Invalid video file' };
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
}

// Export singleton instance
export const apiService = new ApiService();

// Export types for use in components
export type { AnalysisResponse, HealthResponse, PerformanceResponse, SystemStatusResponse, PhaseData };