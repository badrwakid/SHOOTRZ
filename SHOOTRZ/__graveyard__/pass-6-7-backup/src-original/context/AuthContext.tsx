import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { storageService, UserData } from '../services/storage.service';
import { emailService } from '../services/email.service';
import { firebaseService } from '../services/firebase.service';
import { onAuthStateChanged } from 'firebase/auth';

interface AuthContextType {
  user: UserData | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isNewUser: boolean;
  login: (emailOrUsername: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signup: (email: string, password: string, name: string, username: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  updateProfile: (updates: Partial<UserData>) => Promise<void>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>;
  markOnboardingComplete: () => void;
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;
  signInWithApple: () => Promise<{ success: boolean; error?: string }>;
  setUser: (user: UserData | null) => void;
  setIsNewUser: (isNew: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);

  // Load user data on app start
  useEffect(() => {
    let unsubscribe: (() => void) | undefined;
    
    const initializeAuth = async () => {
      console.log('🚀 Starting authentication initialization...');
      unsubscribe = await loadUser();
      console.log('✅ Authentication initialization completed');
    };
    
    initializeAuth();
    
    // Cleanup function
    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, []);

  const loadUser = async (): Promise<(() => void) | undefined> => {
    try {
      console.log('🔄 Loading user...');
      
      // Check Firebase authentication first
      if (firebaseService.isInitialized()) {
        console.log('🔥 Firebase initialized, checking auth state...');
        
        // Add a small delay to ensure Firebase is fully ready
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Set up Firebase auth state listener
        const auth = firebaseService.getAuth();
        if (auth) {
          console.log('🔐 Setting up auth state listener...');
          // Set up the listener
          const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            console.log('🔐 Auth state changed:', firebaseUser ? `User logged in: ${firebaseUser.email}` : 'User logged out');
            console.log('🔐 Firebase user object:', firebaseUser);
            
            if (firebaseUser) {
              // User is authenticated with Firebase
              console.log('👤 Loading Firebase user profile...');
              try {
                const userProfile = await firebaseService.getUserProfile(firebaseUser.uid);
                
                if (userProfile) {
                  // Convert Firebase user to our UserData format
                  const userData: UserData = {
                    id: firebaseUser.uid,
                    email: firebaseUser.email || '',
                    username: userProfile.username || '',
                    name: userProfile.name || '',
                    skillLevel: userProfile.skillLevel || 'beginner',
                    position: userProfile.position || 'Guard',
                    goals: userProfile.goals || [],
                    preferences: userProfile.preferences || {
                      notifications: true,
                      darkMode: true,
                      analytics: true,
                      defaultWorkoutDuration: 30,
                    },
                    createdAt: userProfile.createdAt || new Date().toISOString(),
                    authProvider: 'firebase',
                  };
                  
                  // Save to local storage as backup
                  await storageService.saveUserData(userData);
                  
                  setUser(userData);
                  setIsNewUser(false); // Existing Firebase user
                  console.log('✅ Firebase user loaded successfully:', userData.name);
                } else {
                  console.log('⚠️ Firebase user found but no profile in Firestore - creating new profile...');
                  
                  // Create a new profile for this Firebase user
                  const newProfile = {
                    email: firebaseUser.email || '',
                    username: firebaseUser.email?.split('@')[0] || 'user',
                    name: firebaseUser.displayName || 'Basketball Player',
                    skillLevel: 'beginner',
                    position: 'Guard',
                    goals: [],
                    preferences: {
                      notifications: true,
                      darkMode: true,
                      analytics: true,
                      defaultWorkoutDuration: 30,
                    },
                  };
                  
                  try {
                    await firebaseService.createUserProfile(firebaseUser.uid, newProfile);
                    console.log('✅ Created missing Firestore profile');
                    
                    const userData: UserData = {
                      id: firebaseUser.uid,
                      email: firebaseUser.email || '',
                      username: newProfile.username,
                      name: newProfile.name,
                      skillLevel: 'beginner',
                      position: 'Guard',
                      goals: [],
                      preferences: newProfile.preferences,
                      createdAt: new Date().toISOString(),
                      authProvider: 'firebase',
                    };
                    
                    // Save to local storage as backup
                    await storageService.saveUserData(userData);
                    
                    setUser(userData);
                    setIsNewUser(true); // Treat as new user to trigger onboarding
                  } catch (profileError) {
                    console.error('❌ Failed to create profile, signing out user:', profileError);
                    await firebaseService.signOut();
                    setUser(null);
                  }
                }
              } catch (error) {
                console.error('❌ Error loading user profile:', error);
                setUser(null);
              }
            } else {
              // No Firebase user, check local storage as fallback
              console.log('📱 No Firebase user, checking local storage...');
              const userData = await storageService.getUserData();
              if (userData) {
                console.log('✅ Local user found:', userData.name);
                setUser(userData);
              } else {
                console.log('❌ No local user found');
                setUser(null);
              }
            }
            setIsLoading(false);
          });
          
          // Return the unsubscribe function for cleanup
          return unsubscribe;
        } else {
          console.log('❌ Firebase auth not available, using local storage');
          // Firebase auth not available, use local storage
          const userData = await storageService.getUserData();
          setUser(userData);
          setIsLoading(false);
          return undefined;
        }
      } else {
        console.log('❌ Firebase not initialized, using local storage');
        // Firebase not initialized, use local storage
        const userData = await storageService.getUserData();
        setUser(userData);
        setIsLoading(false);
        return undefined;
      }
    } catch (error) {
      console.error('❌ Error loading user:', error);
      setIsLoading(false);
      return undefined;
    }
  };

  const login = async (emailOrUsername: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔐 Starting login process...');
      console.log('📧 Email/Username:', emailOrUsername);
      
      // Validate input
      if (!emailOrUsername || !password) {
        return { success: false, error: 'Email/username and password are required' };
      }

      // Try Firebase authentication first
      if (firebaseService.isInitialized()) {
        let email = emailOrUsername;
        
        // Handle username login
        if (!emailOrUsername.includes('@')) {
          console.log('👤 Username login detected, looking up email...');
          // This is a username - we need to find the email first
          try {
            const userByUsername = await firebaseService.getUserByUsername(emailOrUsername);
            if (userByUsername) {
              email = userByUsername.email;
              console.log('✅ Found email for username:', email);
            } else {
              console.log('❌ Username not found');
              return { success: false, error: 'Invalid credentials' };
            }
          } catch (error) {
            console.error('❌ Username lookup error:', error);
            return { success: false, error: 'Invalid credentials' };
          }
        }

        console.log('🔥 Attempting Firebase sign in with email:', email);
        const result = await firebaseService.signIn(email, password);
        console.log('🔥 Firebase sign in result:', result);
        
        if (result.success && result.user) {
          console.log('✅ Firebase authentication successful');
          console.log('👤 User UID:', result.user.uid);
          console.log('📧 User email:', result.user.email);
          
          // Get user profile from Firestore
          console.log('📄 Fetching user profile from Firestore...');
          const userProfile = await firebaseService.getUserProfile(result.user.uid);
          console.log('📄 Firestore profile:', userProfile);
          
          if (userProfile) {
            // Convert Firebase user to our UserData format
            const userData: UserData = {
              id: result.user.uid,
              email: result.user.email || '',
              username: userProfile.username || '',
              name: userProfile.name || '',
              skillLevel: userProfile.skillLevel || 'beginner',
              position: userProfile.position || 'Guard',
              goals: userProfile.goals || [],
              preferences: userProfile.preferences || {
                notifications: true,
                darkMode: true,
                analytics: true,
                defaultWorkoutDuration: 30,
              },
              createdAt: userProfile.createdAt || new Date().toISOString(),
              authProvider: 'firebase',
            };
            
            console.log('💾 Saving user data to local storage...');
            // Save to local storage as backup (auth listener will also handle this)
            await storageService.saveUserData(userData);
            
            setUser(userData);
            setIsNewUser(false);
            console.log('✅ Login completed successfully');
            return { success: true };
          } else {
            console.log('❌ User exists in Firebase Auth but not in Firestore');
            // User exists in Firebase Auth but not in Firestore - this is the problem!
            // Let's try to create a profile for them
            console.log('🔧 Attempting to create missing Firestore profile...');
            
            try {
              const newProfile = {
                email: result.user.email || '',
                username: result.user.email?.split('@')[0] || 'user',
                name: result.user.displayName || 'Basketball Player',
                skillLevel: 'beginner',
                position: 'Guard',
                goals: [],
                preferences: {
                  notifications: true,
                  darkMode: true,
                  analytics: true,
                  defaultWorkoutDuration: 30,
                },
                createdAt: new Date().toISOString(),
              };
              
              await firebaseService.createUserProfile(result.user.uid, newProfile);
              console.log('✅ Created missing Firestore profile');
              
              const userData: UserData = {
                id: result.user.uid,
                email: result.user.email || '',
                username: newProfile.username,
                name: newProfile.name,
                skillLevel: 'beginner',
                position: 'Guard',
                goals: [],
                preferences: newProfile.preferences,
                createdAt: new Date().toISOString(),
                authProvider: 'firebase',
              };
              
              await storageService.saveUserData(userData);
              setUser(userData);
              setIsNewUser(true); // Treat as new user to trigger onboarding
              console.log('✅ Login completed with new profile');
              return { success: true };
            } catch (profileError) {
              console.error('❌ Failed to create profile:', profileError);
              return { success: false, error: 'User profile not found. Please contact support.' };
            }
          }
        } else {
          console.log('❌ Firebase authentication failed:', result.error);
          return { success: false, error: result.error || 'Login failed' };
        }
      } else {
        console.log('❌ Firebase not initialized, using local storage fallback');
        // Fallback to local storage if Firebase is not initialized
        const storedUser = await storageService.getUserData();
        
        if (!storedUser) {
          return { success: false, error: 'No account found. Please sign up first.' };
        }

        // Check if input is email or username
        const isEmail = emailOrUsername.includes('@');
        const isMatch = isEmail 
          ? storedUser.email === emailOrUsername
          : storedUser.username === emailOrUsername;

        if (isMatch) {
          setUser(storedUser);
          setIsNewUser(false);
          return { success: true };
        } else {
          return { success: false, error: 'Invalid credentials' };
        }
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      return { success: false, error: 'Login failed. Please try again.' };
    }
  };

  const signup = async (email: string, password: string, name: string, username: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('📝 Starting signup process...');
      console.log('📧 Email:', email);
      console.log('👤 Username:', username);
      console.log('👤 Name:', name);
      
      // Validate input
      if (!email || !password || !name || !username) {
        return { success: false, error: 'All fields are required' };
      }

      if (!isValidEmail(email)) {
        return { success: false, error: 'Invalid email format' };
      }

      if (password.length < 6) {
        return { success: false, error: 'Password must be at least 6 characters' };
      }

      if (username.length < 3) {
        return { success: false, error: 'Username must be at least 3 characters' };
      }

      if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        return { success: false, error: 'Username can only contain letters, numbers, and underscores' };
      }

      // Try Firebase authentication first
      if (firebaseService.isInitialized()) {
        console.log('🔥 Attempting Firebase signup...');
        const result = await firebaseService.signUp(email, password, name);
        console.log('🔥 Firebase signup result:', result);
        
        if (result.success && result.user) {
          console.log('✅ Firebase authentication successful');
          console.log('👤 User UID:', result.user.uid);
          
          // Create user profile in Firestore with username
          const userProfile = {
            email,
            username,
            name,
            skillLevel: 'beginner',
            position: 'Guard',
            goals: [],
            preferences: {
              notifications: true,
              darkMode: true,
              analytics: true,
              defaultWorkoutDuration: 30,
            },
            createdAt: new Date().toISOString(),
          };

          console.log('📄 Creating Firestore profile...');
          await firebaseService.createUserProfile(result.user.uid, userProfile);
          console.log('✅ Firestore profile created');

          // Convert to our UserData format
          const userData: UserData = {
            id: result.user.uid,
            email: result.user.email || '',
            username,
            name,
            skillLevel: 'beginner',
            position: 'Guard',
            goals: [],
            preferences: {
              notifications: true,
              darkMode: true,
              analytics: true,
              defaultWorkoutDuration: 30,
            },
            createdAt: new Date().toISOString(),
            authProvider: 'firebase',
          };

          console.log('💾 Saving user data to local storage...');
          // Save to local storage as backup (auth listener will also handle this)
          await storageService.saveUserData(userData);

          setUser(userData);
          setIsNewUser(true); // Mark as new user for onboarding
          console.log('✅ Signup completed successfully');
          return { success: true };
        } else {
          console.log('❌ Firebase signup failed:', result.error);
          
          // Handle specific error cases
          if (result.error === 'Email already in use') {
            console.log('📧 Email already exists, suggesting login instead...');
            return { 
              success: false, 
              error: 'An account with this email already exists. Please try logging in instead.' 
            };
          }
          
          return { success: false, error: result.error || 'Signup failed' };
        }
      } else {
        console.log('❌ Firebase not initialized, using local storage fallback');
        // Fallback to local storage if Firebase is not initialized
        const existingUser = await storageService.getUserData();
        if (existingUser) {
          return { success: false, error: 'An account already exists. Please login.' };
        }

        const usernameAvailable = await storageService.isUsernameAvailable(username);
        if (!usernameAvailable) {
          return { success: false, error: 'Username already taken. Please choose another.' };
        }

        const newUser: UserData = {
          id: Date.now().toString(),
          email,
          username,
          name,
          skillLevel: 'beginner',
          position: 'Guard',
          goals: [],
          preferences: {
            notifications: true,
            darkMode: true,
            analytics: true,
            defaultWorkoutDuration: 30,
          },
          createdAt: new Date().toISOString(),
          authProvider: 'email',
        };

        await storageService.saveUserData(newUser);
        setUser(newUser);
        setIsNewUser(true);
        return { success: true };
      }
    } catch (error) {
      console.error('❌ Signup error:', error);
      return { success: false, error: 'Signup failed. Please try again.' };
    }
  };

  const markOnboardingComplete = () => {
    setIsNewUser(false);
  };

  const logout = async () => {
    try {
      // Clear all auth state
      setUser(null);
      setIsNewUser(false);
      
      // Always clear local storage
      await storageService.clearAllData();
      console.log('✅ Local storage cleared');
      
      // Sign out from Firebase if initialized
      if (firebaseService.isInitialized()) {
        await firebaseService.signOut();
        console.log('✅ User logged out from Firebase successfully');
      }
      
      console.log('✅ Logout completed successfully');
    } catch (error) {
      console.error('❌ Logout error:', error);
      throw error;
    }
  };

  const updateProfile = async (updates: Partial<UserData>) => {
    try {
      if (!user) return;

      const updatedUser = { ...user, ...updates };
      await storageService.updateUserData(updates);
      setUser(updatedUser);
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  };

  const resetPassword = async (email: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔐 Starting password reset process...');
      console.log('📧 Email:', email);
      
      if (!email) {
        return { success: false, error: 'Email is required' };
      }

      if (!isValidEmail(email)) {
        return { success: false, error: 'Invalid email format' };
      }

      // Use Firebase password reset if initialized
      if (firebaseService.isInitialized()) {
        console.log('🔍 Checking if account exists...');
        
        // First, check if the user exists in our Firestore database
        const userExists = await firebaseService.checkUserExistsByEmail(email);
        
        if (!userExists) {
          console.log('❌ No account found with this email');
          return { success: false, error: 'No account found with this email address' };
        }
        
        console.log('✅ Account exists, sending password reset email');
        console.log('🔥 Using Firebase to send password reset email');
        const result = await firebaseService.resetPassword(email);
        
        if (result.success) {
          console.log('✅ Password reset email sent successfully');
          return { success: true };
        } else {
          console.log('❌ Password reset failed:', result.error);
          return { success: false, error: result.error };
        }
      } else {
        console.log('❌ Firebase not initialized, using email service fallback');
        // Fallback: Check if user exists in local storage
        const storedUser = await storageService.getUserData();
        
        if (!storedUser || storedUser.email !== email) {
          return { success: false, error: 'No account found with this email' };
        }

        // Send password reset email using email service
        const emailResult = await emailService.sendPasswordResetEmail(email);
        
        if (emailResult.success) {
          return { success: true };
        } else {
          return { success: false, error: emailResult.error || 'Failed to send reset email' };
        }
      }
    } catch (error) {
      console.error('❌ Password reset error:', error);
      return { success: false, error: 'Password reset failed. Please try again.' };
    }
  };

  const signInWithGoogle = async (): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔵 Initiating Google Sign-In...');
      
      // Note: This requires proper setup in Firebase Console and Google Cloud Console
      // See SOCIAL_AUTH_SETUP.md for complete setup instructions
      
      // For now, return an informative error
      // TODO: Uncomment the line below after completing setup
      // const result = await socialAuthService.signInWithGoogle();
      
      return { 
        success: false, 
        error: 'Google Sign-In requires additional setup. Please follow the instructions in SOCIAL_AUTH_SETUP.md' 
      };
      
      // After setup, use this code:
      /*
      const result = await socialAuthService.signInWithGoogle();
      
      if (result.success && result.user) {
        setUser(result.user);
        setIsNewUser(result.isNewUser || false);
        return { success: true };
      }
      
      return { success: false, error: result.error };
      */
    } catch (error: any) {
      console.error('❌ Google sign-in error:', error);
      return { success: false, error: error.message || 'Google sign-in failed' };
    }
  };

  const signInWithApple = async (): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🍎 Initiating Apple Sign-In...');
      
      // Note: This requires proper setup in Firebase Console and Apple Developer Portal
      // See SOCIAL_AUTH_SETUP.md for complete setup instructions
      
      // For now, return an informative error
      // TODO: Uncomment the line below after completing setup
      // const result = await socialAuthService.signInWithApple();
      
      return { 
        success: false, 
        error: 'Apple Sign-In requires additional setup. Please follow the instructions in SOCIAL_AUTH_SETUP.md' 
      };
      
      // After setup, use this code:
      /*
      const result = await socialAuthService.signInWithApple();
      
      if (result.success && result.user) {
        setUser(result.user);
        setIsNewUser(result.isNewUser || false);
        return { success: true };
      }
      
      return { success: false, error: result.error };
      */
    } catch (error: any) {
      console.error('❌ Apple sign-in error:', error);
      return { success: false, error: error.message || 'Apple sign-in failed' };
    }
  };

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    isNewUser,
    login,
    signup,
    logout,
    updateProfile,
    resetPassword,
    markOnboardingComplete,
    signInWithGoogle,
    signInWithApple,
    setUser,
    setIsNewUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
