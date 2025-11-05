// Firebase Service for Production-Ready Backend
import { initializeApp, FirebaseApp } from 'firebase/app';
import { 
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithCredential,
  GoogleAuthProvider,
  OAuthProvider,
  signOut,
  sendPasswordResetEmail,
  User,
  Auth,
  UserCredential
} from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { 
  getFirestore, 
  collection, 
  doc, 
  setDoc, 
  getDoc, 
  updateDoc, 
  deleteDoc,
  query,
  where,
  getDocs,
  orderBy,
  limit,
  Firestore
} from 'firebase/firestore';
import { 
  getStorage, 
  ref, 
  uploadBytes, 
  getDownloadURL,
  deleteObject,
  FirebaseStorage
} from 'firebase/storage';

// Firebase configuration
import { FIREBASE_CONFIG } from '../config/firebase.config';

const firebaseConfig = FIREBASE_CONFIG;

class FirebaseService {
  private app: FirebaseApp | null = null;
  private auth: Auth | null = null;
  private db: Firestore | null = null;
  private storage: FirebaseStorage | null = null;
  private initialized = false;

  initialize() {
    if (this.initialized) return;

    try {
      this.app = initializeApp(firebaseConfig);
      // Initialize Auth - Firebase will handle persistence automatically in React Native
      this.auth = getAuth(this.app);
      this.db = getFirestore(this.app);
      this.storage = getStorage(this.app);
      this.initialized = true;
      console.log('Firebase initialized successfully');
    } catch (error) {
      console.error('Firebase initialization error:', error);
      // Gracefully degrade to local storage if Firebase fails
      this.initialized = false;
    }
  }

  isInitialized(): boolean {
    return this.initialized;
  }

  // ==================== AUTHENTICATION ====================

  async signUp(email: string, password: string, name: string): Promise<{ success: boolean; error?: string; user?: User }> {
    if (!this.auth) {
      return { success: false, error: 'Firebase not initialized' };
    }

    try {
      const userCredential = await createUserWithEmailAndPassword(this.auth, email, password);
      const user = userCredential.user;

      // Create user profile in Firestore
      await this.createUserProfile(user.uid, {
        email,
        name,
        skillLevel: 'beginner',
        position: 'Guard',
        createdAt: new Date().toISOString(),
      });

      return { success: true, user };
    } catch (error: any) {
      let errorMessage = 'Signup failed';
      
      if (error.code === 'auth/email-already-in-use') {
        errorMessage = 'Email already in use';
      } else if (error.code === 'auth/weak-password') {
        errorMessage = 'Password too weak';
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = 'Invalid email format';
      }

      return { success: false, error: errorMessage };
    }
  }

  async signIn(email: string, password: string): Promise<{ success: boolean; error?: string; user?: User }> {
    if (!this.auth) {
      return { success: false, error: 'Firebase not initialized' };
    }

    try {
      const userCredential = await signInWithEmailAndPassword(this.auth, email, password);
      return { success: true, user: userCredential.user };
    } catch (error: any) {
      let errorMessage = 'Invalid credentials';
      
      if (error.code === 'auth/user-not-found') {
        errorMessage = 'Invalid credentials';
      } else if (error.code === 'auth/wrong-password') {
        errorMessage = 'Invalid credentials';
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = 'Invalid credentials';
      } else if (error.code === 'auth/too-many-requests') {
        errorMessage = 'Too many failed attempts. Please try again later.';
      }

      return { success: false, error: errorMessage };
    }
  }

  async signInWithGoogle(idToken: string): Promise<{ success: boolean; error?: string; user?: User }> {
    if (!this.auth) {
      return { success: false, error: 'Firebase not initialized' };
    }

    try {
      const credential = GoogleAuthProvider.credential(idToken);
      const userCredential = await signInWithCredential(this.auth, credential);
      return { success: true, user: userCredential.user };
    } catch (error: any) {
      console.error('Google sign-in error:', error);
      return { success: false, error: 'Google sign-in failed' };
    }
  }

  async signInWithApple(idToken: string, nonce?: string): Promise<{ success: boolean; error?: string; user?: User }> {
    if (!this.auth) {
      return { success: false, error: 'Firebase not initialized' };
    }

    try {
      const provider = new OAuthProvider('apple.com');
      const credential = provider.credential({
        idToken,
        rawNonce: nonce,
      });
      const userCredential = await signInWithCredential(this.auth, credential);
      return { success: true, user: userCredential.user };
    } catch (error: any) {
      console.error('Apple sign-in error:', error);
      return { success: false, error: 'Apple sign-in failed' };
    }
  }

  async signOut(): Promise<void> {
    if (!this.auth) throw new Error('Firebase not initialized');
    await signOut(this.auth);
  }

  async resetPassword(email: string): Promise<{ success: boolean; error?: string }> {
    if (!this.auth) {
      return { success: false, error: 'Firebase not initialized' };
    }

    try {
      await sendPasswordResetEmail(this.auth, email);
      return { success: true };
    } catch (error: any) {
      let errorMessage = 'Password reset failed';
      
      if (error.code === 'auth/user-not-found') {
        errorMessage = 'No account found with this email';
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = 'Invalid email format';
      }

      return { success: false, error: errorMessage };
    }
  }

  getCurrentUser(): User | null {
    return this.auth?.currentUser || null;
  }

  getAuth(): Auth | null {
    return this.auth;
  }

  // ==================== FIRESTORE DATABASE ====================

  async createUserProfile(userId: string, data: any): Promise<void> {
    if (!this.db) throw new Error('Firestore not initialized');

    try {
      const userRef = doc(this.db, 'users', userId);
      await setDoc(userRef, {
        ...data,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });

      // Username lookup creation temporarily disabled
      // if (data.username) {
      //   const usernameLookupRef = doc(this.db, 'username_lookup', data.username);
      //   await setDoc(usernameLookupRef, {
      //     userId: userId,
      //     email: data.email,
      //     username: data.username,
      //   });
      // }
    } catch (error) {
      console.error('Error creating user profile:', error);
      throw error;
    }
  }

  async getUserProfile(userId: string): Promise<any | null> {
    if (!this.db) return null;

    try {
      const userRef = doc(this.db, 'users', userId);
      const userSnap = await getDoc(userRef);
      
      if (userSnap.exists()) {
        return { id: userSnap.id, ...userSnap.data() };
      }
      return null;
    } catch (error) {
      console.error('Error getting user profile:', error);
      return null;
    }
  }

  async getUserByUsername(username: string): Promise<any | null> {
    if (!this.db) return null;

    try {
      const usersRef = collection(this.db, 'users');
      const q = query(usersRef, where('username', '==', username));
      const querySnapshot = await getDocs(q);
      
      if (!querySnapshot.empty) {
        const userDoc = querySnapshot.docs[0];
        return { id: userDoc.id, ...userDoc.data() };
      }
      return null;
    } catch (error) {
      console.error('Error getting user by username:', error);
      return null;
    }
  }

  async checkUserExistsByEmail(email: string): Promise<boolean> {
    if (!this.db) return false;

    try {
      console.log('🔍 Checking if user exists with email:', email);
      const usersRef = collection(this.db, 'users');
      const q = query(usersRef, where('email', '==', email), limit(1));
      const querySnapshot = await getDocs(q);
      
      const exists = !querySnapshot.empty;
      console.log(exists ? '✅ User exists' : '❌ User does not exist');
      return exists;
    } catch (error) {
      console.error('❌ Error checking if user exists:', error);
      return false;
    }
  }

  async updateUserProfile(userId: string, updates: any): Promise<void> {
    if (!this.db) throw new Error('Firestore not initialized');

    try {
      const userRef = doc(this.db, 'users', userId);
      await updateDoc(userRef, {
        ...updates,
        updatedAt: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Error updating user profile:', error);
      throw error;
    }
  }

  async deleteUserProfile(userId: string): Promise<void> {
    if (!this.db) throw new Error('Firestore not initialized');

    try {
      const userRef = doc(this.db, 'users', userId);
      await deleteDoc(userRef);
    } catch (error) {
      console.error('Error deleting user profile:', error);
      throw error;
    }
  }

  async deleteUserAccount(): Promise<{ success: boolean; error?: string }> {
    if (!this.auth) {
      return { success: false, error: 'Firebase not initialized' };
    }

    try {
      console.log('🗑️ Starting account deletion process...');
      
      const currentUser = this.auth.currentUser;
      if (!currentUser) {
        console.log('❌ No user is currently signed in');
        return { success: false, error: 'No user is currently signed in' };
      }

      const userId = currentUser.uid;
      const userEmail = currentUser.email;
      console.log('👤 Deleting account for user:', userEmail, '(UID:', userId, ')');

      // Step 1: Delete user profile from Firestore
      console.log('📄 Step 1: Deleting user profile from Firestore...');
      try {
        await this.deleteUserProfile(userId);
        console.log('✅ User profile deleted from Firestore');
      } catch (error) {
        console.warn('⚠️ Failed to delete user profile (may not exist):', error);
        // Continue anyway - profile might not exist
      }

      // Step 2: Delete all user data (analyses, goals, workouts, etc.)
      if (this.db) {
        console.log('📊 Step 2: Deleting user data from collections...');
        const collections = ['analyses', 'goals', 'workouts'];
        for (const collectionName of collections) {
          try {
            const q = query(collection(this.db, collectionName), where('userId', '==', userId));
            const querySnapshot = await getDocs(q);
            const deletePromises = querySnapshot.docs.map(doc => deleteDoc(doc.ref));
            await Promise.all(deletePromises);
            console.log(`✅ Deleted ${querySnapshot.docs.length} documents from ${collectionName}`);
          } catch (error) {
            console.warn(`⚠️ Failed to delete data from ${collectionName}:`, error);
            // Continue anyway
          }
        }
      }

      // Step 3: Delete the Firebase Auth user
      console.log('🔐 Step 3: Deleting Firebase Auth user...');
      await currentUser.delete();
      console.log('✅ Firebase Auth user deleted successfully');

      console.log('🎉 Account deletion completed successfully');
      return { success: true };
    } catch (error: any) {
      console.error('❌ Error deleting user account:', error);
      console.error('❌ Error code:', error.code);
      console.error('❌ Error message:', error.message);
      
      // If deletion fails due to requiring recent authentication
      if (error.code === 'auth/requires-recent-login') {
        console.log('🔐 User needs to re-authenticate');
        return { success: false, error: 'For security, please log out and log back in before deleting your account.' };
      }
      
      return { success: false, error: error.message || 'Failed to delete account' };
    }
  }

  // ==================== ANALYSIS RESULTS ====================

  async saveAnalysisResult(userId: string, analysis: any): Promise<string> {
    if (!this.db) throw new Error('Firestore not initialized');

    try {
      const analysisRef = doc(collection(this.db, 'analyses'));
      await setDoc(analysisRef, {
        userId,
        ...analysis,
        timestamp: new Date().toISOString(),
      });
      return analysisRef.id;
    } catch (error) {
      console.error('Error saving analysis:', error);
      throw error;
    }
  }

  async getUserAnalyses(userId: string, limitCount: number = 100): Promise<any[]> {
    if (!this.db) return [];

    try {
      const analysesRef = collection(this.db, 'analyses');
      const q = query(
        analysesRef,
        where('userId', '==', userId),
        orderBy('timestamp', 'desc'),
        limit(limitCount)
      );
      
      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } catch (error) {
      console.error('Error getting analyses:', error);
      return [];
    }
  }

  // ==================== GOALS ====================

  async saveGoal(userId: string, goal: any): Promise<string> {
    if (!this.db) throw new Error('Firestore not initialized');

    try {
      const goalRef = doc(collection(this.db, 'goals'));
      await setDoc(goalRef, {
        userId,
        ...goal,
        createdAt: new Date().toISOString(),
      });
      return goalRef.id;
    } catch (error) {
      console.error('Error saving goal:', error);
      throw error;
    }
  }

  async getUserGoals(userId: string): Promise<any[]> {
    if (!this.db) return [];

    try {
      const goalsRef = collection(this.db, 'goals');
      const q = query(
        goalsRef,
        where('userId', '==', userId),
        orderBy('createdAt', 'desc')
      );
      
      const querySnapshot = await getDocs(q);
      return querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } catch (error) {
      console.error('Error getting goals:', error);
      return [];
    }
  }

  async updateGoal(goalId: string, updates: any): Promise<void> {
    if (!this.db) throw new Error('Firestore not initialized');

    try {
      const goalRef = doc(this.db, 'goals', goalId);
      await updateDoc(goalRef, {
        ...updates,
        updatedAt: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Error updating goal:', error);
      throw error;
    }
  }

  async deleteGoal(goalId: string): Promise<void> {
    if (!this.db) throw new Error('Firestore not initialized');

    try {
      const goalRef = doc(this.db, 'goals', goalId);
      await deleteDoc(goalRef);
    } catch (error) {
      console.error('Error deleting goal:', error);
      throw error;
    }
  }

  // ==================== STORAGE ====================

  async uploadVideo(userId: string, videoBlob: Blob, filename: string): Promise<string> {
    if (!this.storage) throw new Error('Storage not initialized');

    try {
      const videoRef = ref(this.storage, `videos/${userId}/${filename}`);
      const snapshot = await uploadBytes(videoRef, videoBlob);
      const downloadURL = await getDownloadURL(snapshot.ref);
      return downloadURL;
    } catch (error) {
      console.error('Error uploading video:', error);
      throw error;
    }
  }

  async deleteVideo(videoPath: string): Promise<void> {
    if (!this.storage) throw new Error('Storage not initialized');

    try {
      const videoRef = ref(this.storage, videoPath);
      await deleteObject(videoRef);
    } catch (error) {
      console.error('Error deleting video:', error);
      throw error;
    }
  }
}

// Singleton instance
export const firebaseService = new FirebaseService();

// Auto-initialize
try {
  firebaseService.initialize();
} catch (error) {
  console.warn('Firebase initialization failed - using local storage fallback');
}
