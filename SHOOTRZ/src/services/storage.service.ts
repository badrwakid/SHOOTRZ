// Data persistence service using AsyncStorage
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface UserData {
  id: string;
  email: string;
  username: string; // Unique username for login
  name: string;
  skillLevel: 'beginner' | 'intermediate' | 'advanced';
  position: string;
  goals: Goal[];
  preferences: UserPreferences;
  createdAt: string;
  authProvider?: 'email' | 'google' | 'apple' | 'firebase' | 'supabase'; // How user signed up
}

export interface Goal {
  id: string;
  title: string;
  description: string;
  target: number;
  current: number;
  unit: string;
  deadline: string;
  completed: boolean;
  createdAt: string;
}

export interface UserPreferences {
  notifications: boolean;
  darkMode: boolean;
  analytics: boolean;
  defaultWorkoutDuration: number;
}

export interface AnalysisResult {
  id: string;
  userId: string;
  timestamp: string;
  runId?: string; // Backend run_id for MVP analysis artifacts
  scores: {
    elbow: number;
    balance: number;
    release: number;
    alignment: number;
    total: number;
  };
  feedback: string[];
  angles: {
    elbow: number;
    knee: number;
    release: number;
    bodyAlignment: number;
  };
  mvp?: {
    scoreComponents?: Array<{
      name: string;
      value: number;
      weight: number;
    }>;
    keyFrameImages?: {
      start?: string;
      crouch?: string;
      release?: string;
      end?: string;
    };
    shotWindow?: {
      start_frame?: number;
      crouch_frame?: number;
      release_frame?: number;
      end_frame?: number;
      confidence?: string;
    };
    events?: {
      start?: {
        frame?: number | null;
        timestamp?: number | null;
        status?: string;
        confidence?: number;
        reason_codes?: string[];
      };
      crouch?: {
        frame?: number | null;
        timestamp?: number | null;
        status?: string;
        confidence?: number;
        reason_codes?: string[];
      };
      release?: {
        frame?: number | null;
        timestamp?: number | null;
        status?: string;
        confidence?: number;
        reason_codes?: string[];
      };
      end?: {
        frame?: number | null;
        timestamp?: number | null;
        status?: string;
        confidence?: number;
        reason_codes?: string[];
      };
    };
    diagnostics?: Record<string, unknown>;
  };
}

class StorageService {
  private readonly KEYS = {
    USER_DATA: '@shootrz_user_data',
    ANALYSIS_HISTORY: '@shootrz_analysis_history',
    GOALS: '@shootrz_goals',
    PREFERENCES: '@shootrz_preferences',
    WORKOUT_HISTORY: '@shootrz_workout_history',
  };

  // User Data Management
  async saveUserData(userData: UserData): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.USER_DATA, JSON.stringify(userData));
    } catch (error) {
      console.error('Error saving user data:', error);
      throw error;
    }
  }

  async getUserData(): Promise<UserData | null> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.USER_DATA);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting user data:', error);
      return null;
    }
  }

  async updateUserData(updates: Partial<UserData>): Promise<void> {
    try {
      const currentData = await this.getUserData();
      if (currentData) {
        const updatedData = { ...currentData, ...updates };
        await this.saveUserData(updatedData);
      }
    } catch (error) {
      console.error('Error updating user data:', error);
      throw error;
    }
  }

  // Analysis History
  async saveAnalysisResult(result: AnalysisResult): Promise<void> {
    try {
      const history = await this.getAnalysisHistory();
      const updatedHistory = [result, ...history].slice(0, 100); // Keep last 100 analyses
      await AsyncStorage.setItem(this.KEYS.ANALYSIS_HISTORY, JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Error saving analysis result:', error);
      throw error;
    }
  }

  async getAnalysisHistory(): Promise<AnalysisResult[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.ANALYSIS_HISTORY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting analysis history:', error);
      return [];
    }
  }

  // Goals Management
  async saveGoals(goals: Goal[]): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.GOALS, JSON.stringify(goals));
    } catch (error) {
      console.error('Error saving goals:', error);
      throw error;
    }
  }

  async getGoals(): Promise<Goal[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.GOALS);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting goals:', error);
      return [];
    }
  }

  async addGoal(goal: Goal): Promise<void> {
    try {
      const goals = await this.getGoals();
      goals.push(goal);
      await this.saveGoals(goals);
    } catch (error) {
      console.error('Error adding goal:', error);
      throw error;
    }
  }

  async updateGoal(goalId: string, updates: Partial<Goal>): Promise<void> {
    try {
      const goals = await this.getGoals();
      const goalIndex = goals.findIndex((g) => g.id === goalId);
      if (goalIndex !== -1) {
        goals[goalIndex] = { ...goals[goalIndex], ...updates };
        await this.saveGoals(goals);
      }
    } catch (error) {
      console.error('Error updating goal:', error);
      throw error;
    }
  }

  // User Preferences
  async savePreferences(preferences: UserPreferences): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.PREFERENCES, JSON.stringify(preferences));
    } catch (error) {
      console.error('Error saving preferences:', error);
      throw error;
    }
  }

  async getPreferences(): Promise<UserPreferences> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.PREFERENCES);
      return data
        ? JSON.parse(data)
        : {
            notifications: true,
            darkMode: true,
            analytics: true,
            defaultWorkoutDuration: 30,
          };
    } catch (error) {
      console.error('Error getting preferences:', error);
      return {
        notifications: true,
        darkMode: true,
        analytics: true,
        defaultWorkoutDuration: 30,
      };
    }
  }

  // Workout History
  async saveWorkoutSession(session: any): Promise<void> {
    try {
      const history = await this.getWorkoutHistory();
      history.push(session);
      await AsyncStorage.setItem(this.KEYS.WORKOUT_HISTORY, JSON.stringify(history));
    } catch (error) {
      console.error('Error saving workout session:', error);
      throw error;
    }
  }

  async getWorkoutHistory(): Promise<any[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.WORKOUT_HISTORY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting workout history:', error);
      return [];
    }
  }

  // Drill Completion Tracking
  async markDrillCompleted(drillId: string): Promise<void> {
    try {
      const completions = await this.getDrillCompletions();
      completions.push({
        drillId,
        completedAt: new Date().toISOString(),
      });
      await AsyncStorage.setItem('@shootrz_drill_completions', JSON.stringify(completions));
    } catch (error) {
      console.error('Error marking drill completed:', error);
      throw error;
    }
  }

  async getDrillCompletions(): Promise<Array<{ drillId: string; completedAt: string }>> {
    try {
      const data = await AsyncStorage.getItem('@shootrz_drill_completions');
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting drill completions:', error);
      return [];
    }
  }

  async getDrillCompletionCount(drillId: string): Promise<number> {
    try {
      const completions = await this.getDrillCompletions();
      return completions.filter((c) => c.drillId === drillId).length;
    } catch (error) {
      console.error('Error getting drill completion count:', error);
      return 0;
    }
  }

  // Utility Methods
  // Username Management
  async isUsernameAvailable(username: string): Promise<boolean> {
    try {
      const userData = await this.getUserData();
      if (!userData) return true;

      // Check if username matches current user
      return userData.username !== username;
    } catch (error) {
      console.error('Error checking username:', error);
      return true;
    }
  }

  async getUserByUsername(username: string): Promise<UserData | null> {
    try {
      const userData = await this.getUserData();
      if (userData && userData.username === username) {
        return userData;
      }
      return null;
    } catch (error) {
      console.error('Error getting user by username:', error);
      return null;
    }
  }

  async clearAllData(): Promise<void> {
    try {
      // Clear all app data
      await AsyncStorage.multiRemove([
        this.KEYS.USER_DATA,
        this.KEYS.ANALYSIS_HISTORY,
        this.KEYS.GOALS,
        this.KEYS.PREFERENCES,
        this.KEYS.WORKOUT_HISTORY,
        '@shootrz_drill_completions',
        '@shootrz_onboarding_completed',
      ]);

      console.log('All app data cleared successfully');
    } catch (error) {
      console.error('Error clearing all data:', error);
      throw error;
    }
  }

  async exportData(): Promise<string> {
    try {
      const [userData, analysisHistory, goals, preferences, workoutHistory] = await Promise.all([
        this.getUserData(),
        this.getAnalysisHistory(),
        this.getGoals(),
        this.getPreferences(),
        this.getWorkoutHistory(),
      ]);

      const exportData = {
        userData,
        analysisHistory,
        goals,
        preferences,
        workoutHistory,
        exportedAt: new Date().toISOString(),
        appVersion: '1.0.0',
      };

      return JSON.stringify(exportData, null, 2);
    } catch (error) {
      console.error('Error exporting data:', error);
      throw error;
    }
  }
}

export const storageService = new StorageService();
