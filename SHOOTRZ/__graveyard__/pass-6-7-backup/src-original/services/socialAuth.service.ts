// Social Authentication Service for Google and Apple Sign-In
import * as WebBrowser from 'expo-web-browser';
import * as AppleAuthentication from 'expo-apple-authentication';
import * as Crypto from 'expo-crypto';
import { Platform } from 'react-native';
import { firebaseService } from './firebase.service';
import { storageService, UserData } from './storage.service';

// For WebBrowser result dismissal
WebBrowser.maybeCompleteAuthSession();

// Environment variables - Replace these with your actual credentials
export const GOOGLE_WEB_CLIENT_ID = process.env.GOOGLE_WEB_CLIENT_ID || '637121798837-nj0imcffc612qug8iapbcp9mid32e1vu.apps.googleusercontent.com';
export const GOOGLE_IOS_CLIENT_ID = process.env.GOOGLE_IOS_CLIENT_ID || '637121798837-nj0imcffc612qug8iapbcp9mid32e1vu.apps.googleusercontent.com'; // Use Web Client ID for now
export const GOOGLE_ANDROID_CLIENT_ID = process.env.GOOGLE_ANDROID_CLIENT_ID || '637121798837-nj0imcffc612qug8iapbcp9mid32e1vu.apps.googleusercontent.com'; // Use Web Client ID for now

export interface SocialAuthResult {
  success: boolean;
  error?: string;
  user?: UserData;
  isNewUser?: boolean;
}

class SocialAuthService {
  /**
   * Process Google Sign-In result and create/update user
   * This is called from the LoginScreen component after Google.useAuthRequest completes
   * 
   * @param idToken - The ID token from Google authentication
   * @param displayName - Optional display name from Google
   * @param email - Optional email from Google
   */
  async processGoogleSignIn(
    idToken: string, 
    displayName?: string | null, 
    email?: string | null
  ): Promise<SocialAuthResult> {
    try {
      console.log('🔵 Processing Google Sign-In...');

      // Sign in to Firebase with Google credential
      const firebaseResult = await firebaseService.signInWithGoogle(idToken);

      if (!firebaseResult.success || !firebaseResult.user) {
        return { success: false, error: firebaseResult.error };
      }

      // Check if user profile exists in Firestore
      const userProfile = await firebaseService.getUserProfile(firebaseResult.user.uid);

      let userData: UserData;
      let isNewUser = false;

      if (userProfile) {
        // Existing user
        userData = {
          id: firebaseResult.user.uid,
          email: firebaseResult.user.email || email || '',
          username: userProfile.username || '',
          name: userProfile.name || displayName || 'Basketball Player',
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
          authProvider: 'google',
        };
      } else {
        // New user - create profile
        isNewUser = true;
        
        const newProfile = {
          email: firebaseResult.user.email || email || '',
          username: this.generateUsernameFromEmail(firebaseResult.user.email || email || ''),
          name: displayName || 'Basketball Player',
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

        await firebaseService.createUserProfile(firebaseResult.user.uid, newProfile);

        userData = {
          id: firebaseResult.user.uid,
          email: newProfile.email,
          username: newProfile.username,
          name: newProfile.name,
          skillLevel: 'beginner',
          position: 'Guard',
          goals: [],
          preferences: newProfile.preferences,
          createdAt: newProfile.createdAt,
          authProvider: 'google',
        };
      }

      // Save to local storage
      await storageService.saveUserData(userData);

      console.log('✅ Google sign-in completed successfully');
      return { success: true, user: userData, isNewUser };
    } catch (error: any) {
      console.error('❌ Google sign-in error:', error);
      return { success: false, error: error.message || 'Google sign-in failed' };
    }
  }

  /**
   * Sign in with Apple (iOS only)
   */
  async signInWithApple(): Promise<SocialAuthResult> {
    try {
      console.log('🍎 Starting Apple Sign-In...');

      // Check if Apple Sign-In is available (iOS 13+)
      const isAvailable = await AppleAuthentication.isAvailableAsync();
      
      if (!isAvailable) {
        return { 
          success: false, 
          error: 'Apple Sign-In is not available on this device. Requires iOS 13 or later.' 
        };
      }

      // Generate nonce for security
      const nonce = Math.random().toString(36).substring(2, 10);
      const hashedNonce = await Crypto.digestStringAsync(
        Crypto.CryptoDigestAlgorithm.SHA256,
        nonce
      );

      // Request Apple authentication
      const credential = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
        nonce: hashedNonce,
      });

      if (!credential.identityToken) {
        return { success: false, error: 'No identity token received from Apple' };
      }

      console.log('✅ Apple authentication successful');

      // Sign in to Firebase with Apple credential
      const firebaseResult = await firebaseService.signInWithApple(
        credential.identityToken,
        nonce
      );

      if (!firebaseResult.success || !firebaseResult.user) {
        return { success: false, error: firebaseResult.error };
      }

      // Check if user profile exists in Firestore
      const userProfile = await firebaseService.getUserProfile(firebaseResult.user.uid);

      let userData: UserData;
      let isNewUser = false;

      if (userProfile) {
        // Existing user
        userData = {
          id: firebaseResult.user.uid,
          email: firebaseResult.user.email || credential.email || '',
          username: userProfile.username || '',
          name: userProfile.name || this.getAppleUserName(credential) || 'Basketball Player',
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
          authProvider: 'apple',
        };
      } else {
        // New user - create profile
        isNewUser = true;

        const userName = this.getAppleUserName(credential) || 'Basketball Player';
        
        const newProfile = {
          email: firebaseResult.user.email || credential.email || '',
          username: this.generateUsernameFromEmail(firebaseResult.user.email || credential.email || ''),
          name: userName,
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

        await firebaseService.createUserProfile(firebaseResult.user.uid, newProfile);

        userData = {
          id: firebaseResult.user.uid,
          email: newProfile.email,
          username: newProfile.username,
          name: newProfile.name,
          skillLevel: 'beginner',
          position: 'Guard',
          goals: [],
          preferences: newProfile.preferences,
          createdAt: newProfile.createdAt,
          authProvider: 'apple',
        };
      }

      // Save to local storage
      await storageService.saveUserData(userData);

      console.log('✅ Apple sign-in completed successfully');
      return { success: true, user: userData, isNewUser };
    } catch (error: any) {
      if (error.code === 'ERR_CANCELED') {
        return { success: false, error: 'Sign-in cancelled' };
      }
      console.error('❌ Apple sign-in error:', error);
      return { success: false, error: error.message || 'Apple sign-in failed' };
    }
  }

  /**
   * Helper: Extract user name from Apple credential
   */
  private getAppleUserName(credential: AppleAuthentication.AppleAuthenticationCredential): string | null {
    if (credential.fullName) {
      const { givenName, familyName } = credential.fullName;
      if (givenName && familyName) {
        return `${givenName} ${familyName}`;
      } else if (givenName) {
        return givenName;
      } else if (familyName) {
        return familyName;
      }
    }
    return null;
  }

  /**
   * Helper: Generate a unique username from email
   */
  private generateUsernameFromEmail(email: string): string {
    const baseUsername = email.split('@')[0].replace(/[^a-zA-Z0-9]/g, '');
    const randomSuffix = Math.floor(Math.random() * 10000);
    return `${baseUsername}${randomSuffix}`;
  }

  /**
   * Check if Google Sign-In is available
   */
  isGoogleAvailable(): boolean {
    return true; // Google Sign-In works on all platforms with Expo
  }

  /**
   * Check if Apple Sign-In is available
   */
  async isAppleAvailable(): Promise<boolean> {
    if (Platform.OS !== 'ios') {
      return false;
    }
    return await AppleAuthentication.isAvailableAsync();
  }
}

export const socialAuthService = new SocialAuthService();
