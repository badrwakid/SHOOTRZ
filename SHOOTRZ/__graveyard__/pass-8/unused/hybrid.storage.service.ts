// Hybrid Storage Service - Uses Firebase when available, falls back to AsyncStorage
import { storageService as localStorageService, UserData, AnalysisResult, Goal } from './storage.service';
import { firebaseService } from './firebase.service';
import { USE_FIREBASE } from '../config/firebase.config';

class HybridStorageService {
  private useFirebase = USE_FIREBASE && firebaseService.isInitialized();

  // ==================== USER DATA ====================

  async saveUserData(userData: UserData): Promise<void> {
    // Always save locally
    await localStorageService.saveUserData(userData);

    // Also save to Firebase if available
    if (this.useFirebase && userData.id) {
      try {
        await firebaseService.createUserProfile(userData.id, userData);
      } catch (error) {
        console.error('Firebase save error:', error);
        // Continue with local storage only
      }
    }
  }

  async getUserData(): Promise<UserData | null> {
    if (this.useFirebase) {
      try {
        const user = firebaseService.getCurrentUser();
        if (user) {
          const userData = await firebaseService.getUserProfile(user.uid);
          if (userData) {
            // Sync to local storage
            await localStorageService.saveUserData(userData);
            return userData;
          }
        }
      } catch (error) {
        console.error('Firebase fetch error:', error);
      }
    }

    // Fallback to local storage
    return await localStorageService.getUserData();
  }

  async updateUserData(updates: Partial<UserData>): Promise<void> {
    // Always update locally
    await localStorageService.updateUserData(updates);

    // Also update Firebase if available
    if (this.useFirebase) {
      try {
        const user = firebaseService.getCurrentUser();
        if (user) {
          await firebaseService.updateUserProfile(user.uid, updates);
        }
      } catch (error) {
        console.error('Firebase update error:', error);
      }
    }
  }

  // ==================== ANALYSIS RESULTS ====================

  async saveAnalysisResult(result: AnalysisResult): Promise<void> {
    // Always save locally
    await localStorageService.saveAnalysisResult(result);

    // Also save to Firebase if available
    if (this.useFirebase) {
      try {
        await firebaseService.saveAnalysisResult(result.userId, result);
      } catch (error) {
        console.error('Firebase save analysis error:', error);
      }
    }
  }

  async getAnalysisHistory(): Promise<AnalysisResult[]> {
    if (this.useFirebase) {
      try {
        const user = firebaseService.getCurrentUser();
        if (user) {
          const analyses = await firebaseService.getUserAnalyses(user.uid);
          // Sync to local storage
          for (const analysis of analyses) {
            await localStorageService.saveAnalysisResult(analysis);
          }
          return analyses;
        }
      } catch (error) {
        console.error('Firebase fetch analyses error:', error);
      }
    }

    // Fallback to local storage
    return await localStorageService.getAnalysisHistory();
  }

  // ==================== GOALS ====================

  async saveGoals(goals: Goal[]): Promise<void> {
    await localStorageService.saveGoals(goals);

    if (this.useFirebase) {
      try {
        const user = firebaseService.getCurrentUser();
        if (user) {
          for (const goal of goals) {
            await firebaseService.saveGoal(user.uid, goal);
          }
        }
      } catch (error) {
        console.error('Firebase save goals error:', error);
      }
    }
  }

  async getGoals(): Promise<Goal[]> {
    if (this.useFirebase) {
      try {
        const user = firebaseService.getCurrentUser();
        if (user) {
          const goals = await firebaseService.getUserGoals(user.uid);
          // Sync to local
          await localStorageService.saveGoals(goals);
          return goals;
        }
      } catch (error) {
        console.error('Firebase fetch goals error:', error);
      }
    }

    return await localStorageService.getGoals();
  }

  async addGoal(goal: Goal): Promise<void> {
    await localStorageService.addGoal(goal);

    if (this.useFirebase) {
      try {
        const user = firebaseService.getCurrentUser();
        if (user) {
          await firebaseService.saveGoal(user.uid, goal);
        }
      } catch (error) {
        console.error('Firebase add goal error:', error);
      }
    }
  }

  async updateGoal(goalId: string, updates: Partial<Goal>): Promise<void> {
    await localStorageService.updateGoal(goalId, updates);

    if (this.useFirebase) {
      try {
        await firebaseService.updateGoal(goalId, updates);
      } catch (error) {
        console.error('Firebase update goal error:', error);
      }
    }
  }

  // ==================== PASS-THROUGH METHODS ====================
  // These use local storage only (Firebase not critical for these)

  async getPreferences() {
    return await localStorageService.getPreferences();
  }

  async savePreferences(preferences: any) {
    return await localStorageService.savePreferences(preferences);
  }

  async saveWorkoutSession(session: any) {
    return await localStorageService.saveWorkoutSession(session);
  }

  async getWorkoutHistory() {
    return await localStorageService.getWorkoutHistory();
  }

  async markDrillCompleted(drillId: string) {
    return await localStorageService.markDrillCompleted(drillId);
  }

  async getDrillCompletions() {
    return await localStorageService.getDrillCompletions();
  }

  async getDrillCompletionCount(drillId: string) {
    return await localStorageService.getDrillCompletionCount(drillId);
  }

  async clearAllData() {
    await localStorageService.clearAllData();

    if (this.useFirebase) {
      try {
        const user = firebaseService.getCurrentUser();
        if (user) {
          await firebaseService.deleteUserProfile(user.uid);
        }
      } catch (error) {
        console.error('Firebase delete error:', error);
      }
    }
  }

  async exportData() {
    return await localStorageService.exportData();
  }
}

// Export singleton instance
export const hybridStorage = new HybridStorageService();
