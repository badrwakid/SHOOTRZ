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

  /** Local cache key: legacy global or per-user to avoid cross-account bleed. */
  private analysisHistoryStorageKey(userId?: string | null): string {
    if (userId) {
      return `${this.KEYS.ANALYSIS_HISTORY}:${userId}`;
    }
    return this.KEYS.ANALYSIS_HISTORY;
  }

  /**
   * Clear cached analyses for one user (e.g. account switch). Does not clear goals/prefs.
   */
  async clearAnalysisHistoryForUser(userId: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.analysisHistoryStorageKey(userId));
    } catch (error) {
      console.error('Error clearing analysis history for user:', error);
    }
  }

  // Analysis History
  async saveAnalysisResult(
    result: AnalysisResult,
    userId?: string | null,
  ): Promise<void> {
    try {
      const key = this.analysisHistoryStorageKey(userId);
      const history = await this.getAnalysisHistory(userId);
      const updatedHistory = [result, ...history].slice(0, 100); // Keep last 100 analyses
      await AsyncStorage.setItem(key, JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Error saving analysis result:', error);
      throw error;
    }
  }

  async getAnalysisHistory(userId?: string | null): Promise<AnalysisResult[]> {
    try {
      if (userId) {
        const scoped = await AsyncStorage.getItem(this.analysisHistoryStorageKey(userId));
        if (scoped) {
          return JSON.parse(scoped);
        }
      }
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
      // BUG FIX: Cap workout history to prevent unbounded AsyncStorage growth
      const capped = history.slice(-200);
      await AsyncStorage.setItem(this.KEYS.WORKOUT_HISTORY, JSON.stringify(capped));
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
      // BUG FIX: Cap drill completions to prevent unbounded AsyncStorage growth
      const capped = completions.slice(-500);
      await AsyncStorage.setItem('@shootrz_drill_completions', JSON.stringify(capped));
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
      const keys = await AsyncStorage.getAllKeys();
      const analysisScoped = (keys || []).filter(
        (k) =>
          k === this.KEYS.ANALYSIS_HISTORY ||
          k.startsWith(`${this.KEYS.ANALYSIS_HISTORY}:`),
      );
      await AsyncStorage.multiRemove([
        ...analysisScoped,
        this.KEYS.USER_DATA,
        this.KEYS.GOALS,
        this.KEYS.PREFERENCES,
        this.KEYS.WORKOUT_HISTORY,
        '@shootrz_drill_completions',
        '@shootrz_onboarding_completed',
      ]);
    } catch (error) {
      console.error('Error clearing all data:', error);
      throw error;
    }
  }

  /**
   * One-time migration: push locally-cached data to Supabase via API, then
   * clear the local copies.  Gated by a flag so it runs at most once.
   */
  async migrateToSupabase(apiService: any): Promise<void> {
    try {
      const flag = await AsyncStorage.getItem('@shootrz_supabase_migration_v1_complete')
      if (flag === 'true') return

      const [drills, workouts] = await Promise.all([
        this.getDrillCompletions(),
        this.getWorkoutHistory(),
      ])

      for (const drill of drills) {
        try {
          await apiService.completeDrill({
            drillId: drill.drillId,
            drillName: drill.drillId,
          })
        } catch { /* best-effort */ }
      }

      for (const workout of workouts) {
        try {
          await apiService.updateWorkoutProgress(
            workout.workoutId || workout.id || 'unknown',
            { workoutName: workout.workoutName || workout.name || 'Migrated Workout' },
          )
        } catch { /* best-effort */ }
      }

      const keys = await AsyncStorage.getAllKeys()
      const analysisKeys = (keys || []).filter(
        (k) =>
          k === this.KEYS.ANALYSIS_HISTORY ||
          k.startsWith(`${this.KEYS.ANALYSIS_HISTORY}:`),
      )
      await AsyncStorage.multiRemove([
        '@shootrz_drill_completions',
        this.KEYS.WORKOUT_HISTORY,
        ...analysisKeys,
      ])

      await AsyncStorage.setItem('@shootrz_supabase_migration_v1_complete', 'true')
    } catch (error) {
      console.error('Supabase migration failed (will retry next launch):', error)
    }
  }

  async exportData(): Promise<string> {
    try {
      const userData = await this.getUserData();
      const [analysisHistory, goals, preferences, workoutHistory] = await Promise.all([
        this.getAnalysisHistory(userData?.id),
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
