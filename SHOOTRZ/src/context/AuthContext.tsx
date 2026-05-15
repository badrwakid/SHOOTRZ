// BUG FIX: Removed unused startTransition import
import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { storageService, UserData } from '../services/storage.service';
import { supabase } from '../services/supabase.client';
import { apiService } from '../services/api.service';
// BUG FIX: Removed unused openBrowserAsync import (WebBrowser.* is used instead)
import * as AuthSession from 'expo-auth-session';
import * as Linking from 'expo-linking';
import * as WebBrowser from 'expo-web-browser';
import { eventBus } from '../utils/eventBus';

/**
 * Extract PKCE `code` and OAuth errors from Supabase/Google redirect URLs.
 * Codes may appear in the query or in the hash (e.g. #code=...&state=...).
 */
function parseOAuthRedirectUrl(rawUrl: string): {
	code: string | null;
	oauthError: string | null;
	oauthErrorDescription: string | null;
} {
	let oauthError: string | null = null;
	let oauthErrorDescription: string | null = null;
	try {
		const u = new URL(rawUrl);
		let code = u.searchParams.get('code');
		oauthError = u.searchParams.get('error');
		oauthErrorDescription = u.searchParams.get('error_description');
		if (u.hash && u.hash.length > 1) {
			const hp = new URLSearchParams(u.hash.startsWith('#') ? u.hash.slice(1) : u.hash);
			if (!code) {
				code = hp.get('code');
			}
			if (!oauthError) {
				oauthError = hp.get('error');
			}
			if (!oauthErrorDescription) {
				oauthErrorDescription = hp.get('error_description');
			}
		}
		if (oauthErrorDescription) {
			try {
				oauthErrorDescription = decodeURIComponent(
					oauthErrorDescription.replace(/\+/g, ' '),
				);
			} catch {
				/* use raw */
			}
		}
		return { code, oauthError, oauthErrorDescription };
	} catch {
		const codeMatch = rawUrl.match(/(?:^|[?&#])code=([^&#]+)/);
		const errMatch = rawUrl.match(/[?&#]error=([^&#]+)/);
		const descMatch = rawUrl.match(/[?&#]error_description=([^&#]+)/);
		let code: string | null = null;
		if (codeMatch) {
			try {
				code = decodeURIComponent(codeMatch[1]);
			} catch {
				code = codeMatch[1];
			}
		}
		if (errMatch) {
			try {
				oauthError = decodeURIComponent(errMatch[1]);
			} catch {
				oauthError = errMatch[1];
			}
		}
		if (descMatch) {
			try {
				oauthErrorDescription = decodeURIComponent(
					descMatch[1].replace(/\+/g, ' '),
				);
			} catch {
				oauthErrorDescription = descMatch[1];
			}
		}
		return { code, oauthError, oauthErrorDescription };
	}
}

interface AuthContextType {
  user: UserData | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isNewUser: boolean;
  login: (
    emailOrUsername: string,
    password: string
  ) => Promise<{ success: boolean; error?: string }>;
  signup: (
    email: string,
    password: string,
    name: string,
    username: string
  ) => Promise<{ success: boolean; error?: string; requiresEmailConfirmation?: boolean }>;
  logout: () => Promise<void>;
  updateProfile: (updates: Partial<UserData>) => Promise<void>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>;
  markOnboardingComplete: () => Promise<void>;
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;
  signInWithApple: () => Promise<{ success: boolean; error?: string }>;
  setUser: (user: UserData | null) => void;
  setIsNewUser: (isNew: boolean) => void;
  setNavigationCallback: (callback: (() => void) | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);
  
  // Navigation callback ref - allows direct navigation trigger from auth context
  const navigationCallbackRef = React.useRef<(() => void) | null>(null);
  const prevAuthUserIdRef = React.useRef<string | null>(null);
  
  // Expose method to set navigation callback (used by LoginScreen)
  const setNavigationCallback = React.useCallback((callback: (() => void) | null) => {
    navigationCallbackRef.current = callback;
  }, []);

  // Helper function to create user data from Supabase session
  const createUserDataFromSession = React.useCallback(async (u: any): Promise<UserData> => {
    // Extract name from Google metadata
    const googleName = u.user_metadata?.full_name || 
                       u.user_metadata?.name || 
                       u.user_metadata?.display_name || 
                       '';
    
    // Fallback name
    const name = googleName || 'Basketball Player';
    
    return {
      id: u.id,
      email: u.email || '',
      username: u.user_metadata?.username || (u.email?.split('@')[0] || 'user'),
      name,
      skillLevel: 'beginner',
      position: 'Guard',
      goals: [],
      preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
      createdAt: u.created_at || new Date().toISOString(),
      authProvider: (u.app_metadata?.provider || 'supabase') as any,
    };
  }, []);

  // Helper function to check if user is new (non-blocking)
  const checkAndSetIsNewUser = React.useCallback(async (u: any, userData: UserData) => {
    try {
      // Check if user exists in database
      const { data: dbUser, error } = await supabase
        .from('users')
        .select('username, name, has_completed_onboarding')
        .eq('id', u.id)
        .single();
      
      if (error) {
        if (error.code === 'PGRST116') {
          // User not found - create record
          const authProvider = u.app_metadata?.provider || 
                             u.user_metadata?.provider || 
                             (u.email?.includes('@') ? 'email' : 'google');
          
          // Extract Google name
          const googleName = u.user_metadata?.full_name || 
                           u.user_metadata?.name || 
                           u.user_metadata?.display_name || 
                           null;
          
          await supabase.from('users').insert({
            id: u.id,
            email: u.email || '',
            auth_provider: authProvider,
            name: googleName,
            username: null,
          });
          
          setIsNewUser(true);
        } else {
          console.warn('⚠️ Error checking user:', error);
          setIsNewUser(true);
        }
      } else if (dbUser) {
        // User exists - check if they have completed onboarding
        // They need both a real username AND onboarding completion status = true
        const emailPrefix = u.email?.split('@')[0] || 'user';
        const hasUsername = dbUser.username && 
                           dbUser.username.trim() !== '' && 
                           dbUser.username !== 'user' &&
                           dbUser.username !== emailPrefix;
        const hasCompletedOnboarding = dbUser.has_completed_onboarding === true;
        
        // User is new if they haven't completed onboarding
        // If they completed onboarding, they're NOT new (even if username is email-prefix)
        const isNew = !hasCompletedOnboarding;
        setIsNewUser(isNew);
        
        // Update user data with database info if available (consolidate updates)
        const updates: Partial<UserData> = {};
        if (dbUser.name && dbUser.name !== userData.name) {
          updates.name = dbUser.name;
        }
        if (hasUsername && dbUser.username !== userData.username) {
          updates.username = dbUser.username;
        }
        
        if (Object.keys(updates).length > 0) {
          setUser(prev => prev ? { ...prev, ...updates } : null);
        }
      }
    } catch (err: any) {
      console.error('❌ Error checking if new user:', err);
      setIsNewUser(true);
    }
  }, []);

  // Load user data on app start (Supabase)
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();
        
        // Handle network errors gracefully
        if (error) {
          const isNetworkError = 
            error.message?.includes('Network request failed') ||
            error.message?.includes('Network Error') ||
            error.message?.includes('Failed to fetch');
          
          if (isNetworkError) {
            // Network error - fail silently, user is not authenticated
            prevAuthUserIdRef.current = null;
            await storageService.clearAllData();
            setUser(null);
            setIsLoading(false);
            return;
          }
        }
        
        if (data?.session?.user) {
          const u = data.session.user;
          const prior = prevAuthUserIdRef.current;
          if (prior && prior !== u.id) {
            await storageService.clearAnalysisHistoryForUser(prior);
          }
          prevAuthUserIdRef.current = u.id;
          const userData = await createUserDataFromSession(u);
          await storageService.saveUserData(userData);
          setUser(userData);
          setIsNewUser(false);
        } else {
          prevAuthUserIdRef.current = null;
          await storageService.clearAllData();
          setUser(null);
        }
        setIsLoading(false);
      } catch (error: any) {
        // Catch any unexpected errors
        const isNetworkError = 
          error?.message?.includes('Network request failed') ||
          error?.message?.includes('Network Error') ||
          error?.message?.includes('Failed to fetch');
        
        if (!isNetworkError && __DEV__) {
          console.warn('⚠️ Auth initialization error:', error);
        }
        
        prevAuthUserIdRef.current = null;
        await storageService.clearAllData();
        setUser(null);
        setIsLoading(false);
      }
    };
    
    const sub = supabase.auth.onAuthStateChange(async (event, session) => {
      try {
        if (session?.user) {
          const u = session.user;
          const prior = prevAuthUserIdRef.current;
          if (prior && prior !== u.id) {
            await storageService.clearAnalysisHistoryForUser(prior);
          }
          prevAuthUserIdRef.current = u.id;

          // Create user data from session
          const userData = await createUserDataFromSession(u);
          
          // Set user state immediately - this makes isAuthenticated = true
          setUser(userData);
          setIsLoading(false);
          
          // Check if user is new in background (non-blocking)
          checkAndSetIsNewUser(u, userData);
          
          // Save to storage in background
          storageService.saveUserData(userData).catch((err) => 
            console.warn('⚠️ Failed to save user data:', err)
          );
          
          // Trigger navigation callback
          if (navigationCallbackRef.current) {
            setTimeout(() => navigationCallbackRef.current?.(), 50);
          }
        } else {
          prevAuthUserIdRef.current = null;
          await storageService.clearAllData();
          setUser(null);
          setIsNewUser(false);
          setIsLoading(false);
        }
      } catch (error: any) {
        console.error('❌ Error in onAuthStateChange:', error);
        setIsLoading(false);
      }
    });
    
    initializeAuth();
    return () => { sub.data.subscription.unsubscribe(); };
  }, [createUserDataFromSession, checkAndSetIsNewUser]);

  /** Warm server-backed stats/history after sign-in so Home/Progress are not empty on first paint. */
  useEffect(() => {
    if (!user?.id) {
      return;
    }
    void Promise.allSettled([
      apiService.getUserStats(),
      apiService.getUserStreak(),
      apiService.getAnalysisHistory(20, 0),
    ]);
  }, [user?.id]);

  // BUG FIX: Removed empty loadUser function (dead code)

  const login = async (
    emailOrUsername: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      // Validate input
      if (!emailOrUsername || !password) {
        // BUG FIX: Supabase signInWithPassword only accepts email, not username
        return { success: false, error: 'Email and password are required' };
      }

      const email = emailOrUsername;
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error || !data.session?.user) {
        return { success: false, error: error?.message || 'Login failed' };
      }
      const u = data.session.user;
      const userData: UserData = {
        id: u.id,
        email: u.email || '',
        username: u.user_metadata?.username || (u.email?.split('@')[0] || 'user'),
        name: u.user_metadata?.name || 'Basketball Player',
        skillLevel: 'beginner',
        position: 'Guard',
        goals: [],
        preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
        createdAt: new Date().toISOString(),
        authProvider: 'supabase',
      };
      await storageService.saveUserData(userData);
      setUser(userData);
      setIsNewUser(false);
      return { success: true };
    } catch (error) {
      console.error('❌ Login error:', error);
      return { success: false, error: 'Login failed. Please try again.' };
    }
  };

  const signup = async (
    email: string,
    password: string,
    name: string,
    username: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
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
        return {
          success: false,
          error: 'Username can only contain letters, numbers, and underscores',
        };
      }

      // Step 1: Create user in Supabase Auth
      // If email confirmation is enabled, user won't have session yet
      // Database trigger will automatically create users table record
      const { data, error } = await supabase.auth.signUp({ 
        email, 
        password, 
        options: { 
          data: { name, username },
          emailRedirectTo: 'shootrz://confirm-email',
        } 
      });
      
      if (error) {
        console.error('❌ Supabase auth signup error:', error);
        let errorMessage = 'Signup failed. Please try again.';
        
        if (error.message.includes('User already registered')) {
          errorMessage = 'An account with this email already exists. Please sign in instead.';
        } else if (error.message.includes('Invalid email')) {
          errorMessage = 'Please enter a valid email address.';
        } else if (error.message.includes('Password')) {
          errorMessage = 'Password must be at least 6 characters long.';
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
          errorMessage = 'Network error. Please check your internet connection and try again.';
        } else {
          errorMessage = error.message || errorMessage;
        }
        
        return { success: false, error: errorMessage };
      }
      
      if (!data.user) {
        return { success: false, error: 'Signup failed. Please try again.' };
      }
      
      const u = data.user;
      
      // Step 2: Handle database record creation
      // If database trigger is set up, it will automatically create the record
      // Otherwise, try to insert (only works if no email confirmation or session exists)
      
      if (data.session) {
        const { data: userRecord, error: insertError } = await supabase
          .from('users')
          .insert({
            id: u.id,
            email: u.email || email,
            auth_provider: 'supabase',
            name: name,
          })
          .select()
          .single();
        
        if (insertError) {
          console.warn('⚠️ Manual insert failed (trigger may have already created it):', insertError.message);
          // Check if user already exists (trigger might have created it)
          const { data: existing } = await supabase
            .from('users')
            .select('id')
            .eq('id', u.id)
            .single();
          
          if (!existing) {
            console.error('❌ User record not created. Please set up database trigger (see trigger_create_user.sql)');
            return { 
              success: false, 
              error: 'User account created but profile setup failed. Please contact support.' 
            };
          }
        }
      } else {
        // Still create local user data for better UX (user will see "check email" message)
        const userData: UserData = {
          id: u.id,
          email: u.email || email,
          username,
          name,
          skillLevel: 'beginner',
          position: 'Guard',
          goals: [],
          preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
          createdAt: new Date().toISOString(),
          authProvider: 'supabase',
        };
        
        await storageService.saveUserData(userData);
        // Don't set user yet - wait for email confirmation
        setIsNewUser(true);
        return { 
          success: true,
          requiresEmailConfirmation: true
        } as { success: boolean; error?: string; requiresEmailConfirmation?: boolean };
      }
      
      // Step 3: Create user data object and cache locally (only if session exists)
      const userData: UserData = {
        id: u.id,
        email: u.email || email,
        username,
        name,
        skillLevel: 'beginner',
        position: 'Guard',
        goals: [],
        preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
        createdAt: new Date().toISOString(),
        authProvider: 'supabase',
      };
      
      await storageService.saveUserData(userData);
      setUser(userData);
      setIsNewUser(true);
      return { success: true };
    } catch (error) {
      console.error('❌ Signup error:', error);
      return { success: false, error: 'Signup failed. Please try again.' };
    }
  };

  const markOnboardingComplete = async () => {
    setIsNewUser(false);
    
    // Persist via backend API only (frontend should not write users directly).
    if (user?.id) {
      try {
        await apiService.updateUserProfile({ hasCompletedOnboarding: true } as any);
        eventBus.emit('user:updated');
      } catch (error: any) {
        console.error('❌ Failed to save onboarding completion:', error);
      }
    }
  };

  const logout = async () => {
    try {
      // Clear all auth state
      setUser(null);
      setIsNewUser(false);

      // Always clear local storage
      await storageService.clearAllData();

      await supabase.auth.signOut();
    } catch (error) {
      console.error('❌ Logout error:', error);
      throw error;
    }
  };

  const updateProfile = async (updates: Partial<UserData>) => {
    if (!user?.id) {
      console.error('❌ Cannot update profile: No user logged in');
      return;
    }

    try {
      const payload: Record<string, unknown> = {};
      if (updates.username !== undefined) payload.username = updates.username;
      if (updates.name !== undefined) payload.name = updates.name;
      if (updates.skillLevel !== undefined) payload.skillLevel = updates.skillLevel;
      if (updates.position !== undefined) payload.position = updates.position;
      if (updates.primaryGoal !== undefined) payload.primaryGoal = updates.primaryGoal;
      if (updates.trainingFrequency !== undefined) payload.trainingFrequency = updates.trainingFrequency;
      if (updates.preferredDrillDuration !== undefined) {
        payload.preferredDrillDuration = updates.preferredDrillDuration;
      }
      if (updates.dominantHand !== undefined) payload.dominantHand = updates.dominantHand;
      if (updates.yearsPlaying !== undefined) payload.yearsPlaying = updates.yearsPlaying;
      if (updates.coachingStyle !== undefined) payload.coachingStyle = updates.coachingStyle;
      if (updates.age !== undefined) payload.age = updates.age;
      if (updates.heightCm !== undefined) payload.heightCm = updates.heightCm;
      if (updates.weightKg !== undefined) payload.weightKg = updates.weightKg;

      await apiService.updateUserProfile(payload as any);
      eventBus.emit('user:updated');
    } catch (error: any) {
      console.error('❌ Error updating profile:', error);
      throw error;
    }
  };

  const resetPassword = async (email: string): Promise<{ success: boolean; error?: string }> => {
    try {
      if (!email) {
        return { success: false, error: 'Email is required' };
      }

      if (!isValidEmail(email)) {
        return { success: false, error: 'Invalid email format' };
      }

      // Use Supabase password reset with app deep link
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: 'shootrz://reset-password',
      });

      if (error) {
        let errorMessage = 'Failed to send reset email. Please try again.';
        
        if (error.message.includes('User not found')) {
          errorMessage = 'No account found with this email address.';
        } else if (error.message.includes('Email rate limit')) {
          errorMessage = 'Too many reset requests. Please wait a few minutes and try again.';
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
          errorMessage = 'Network error. Please check your internet connection and try again.';
        } else {
          errorMessage = error.message || errorMessage;
        }
        
        return { success: false, error: errorMessage };
      }

      return { success: true };
    } catch (error) {
      console.error('❌ Password reset error:', error);
      return { success: false, error: 'Password reset failed. Please try again.' };
    }
  };

    const signInWithGoogle = async (): Promise<{ success: boolean; error?: string }> => {
      try {
        const redirectUri = AuthSession.makeRedirectUri({
          scheme: 'shootrz',
          path: 'auth/callback',
        });
        // Get OAuth URL from Supabase with the redirect URI
        // Add prompt: 'select_account' to force account picker (always ask which account)
        const { data, error } = await supabase.auth.signInWithOAuth({
          provider: 'google',
          options: {
            redirectTo: redirectUri,
            // RN has no window — we open the URL with WebBrowser; avoid double navigation
            skipBrowserRedirect: true,
            queryParams: {
              prompt: 'select_account', // Force Google to show account picker
            },
          },
        });
        
        if (error) {
          console.error('❌ OAuth initiation error:', error);
          return { success: false, error: error.message };
        }
        
        if (!data?.url) {
          console.error('❌ No OAuth URL returned from Supabase');
          return { success: false, error: 'Failed to generate OAuth URL' };
        }
        
        // Use WebBrowser to handle the OAuth flow
        // This properly handles redirects and returns the result
        WebBrowser.maybeCompleteAuthSession();

        // Some devices return a bare scheme URL from openAuthSessionAsync while the full
        // callback (with ?code=) arrives on Linking — subscribe before opening the browser.
        let oauthUrlFromLinking: string | null = null;
        const linkingSub = Linking.addEventListener('url', ({ url: incoming }) => {
          if (
            incoming.includes('code=') ||
            incoming.includes('error=') ||
            incoming.includes('auth/callback')
          ) {
            oauthUrlFromLinking = incoming;
          }
        });

        let result: WebBrowser.WebBrowserAuthSessionResult;
        try {
          result = await WebBrowser.openAuthSessionAsync(data.url, redirectUri);
        } finally {
          linkingSub.remove();
        }

        if (result.type === 'success') {
          const browserUrl = result.url || '';
          const parsedBrowser = parseOAuthRedirectUrl(browserUrl);
          const linkingRaw = oauthUrlFromLinking;
          const parsedLinking = linkingRaw
            ? parseOAuthRedirectUrl(linkingRaw)
            : null;

          let url = browserUrl;
          let parsed = parsedBrowser;
          if (
            parsedLinking &&
            linkingRaw &&
            (parsedLinking.code || parsedLinking.oauthError) &&
            !parsedBrowser.code &&
            !parsedBrowser.oauthError
          ) {
            url = linkingRaw;
            parsed = parsedLinking;
          } else if (
            parsedLinking &&
            (parsedLinking.code || parsedLinking.oauthError) &&
            parsedBrowser.code
          ) {
            // Prefer WebBrowser URL when both carry a code (canonical callback)
            url = browserUrl;
            parsed = parsedBrowser;
          } else if (
            parsedLinking &&
            linkingRaw &&
            (parsedLinking.code || parsedLinking.oauthError)
          ) {
            url = linkingRaw;
            parsed = parsedLinking;
          }

          let code = parsed.code;

          if (parsed.oauthError) {
            const msg =
              parsed.oauthErrorDescription ||
              parsed.oauthError ||
              'Sign-in was cancelled or denied';
            return { success: false, error: msg };
          }

          // Deep link handler may have exchanged the code already
          const { data: { session: sessionAfterCallback } } = await supabase.auth.getSession();
          if (sessionAfterCallback?.user) {
            const u = sessionAfterCallback.user;
            const userData: UserData = {
              id: u.id,
              email: u.email || '',
              username: u.user_metadata?.username || u.email?.split('@')[0] || 'user',
              name: u.user_metadata?.name || 'Basketball Player',
              skillLevel: 'beginner',
              position: 'Guard',
              goals: [],
              preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
              createdAt: u.created_at || new Date().toISOString(),
              authProvider: 'supabase',
            };
            setUser(userData);
            setIsLoading(false);
            if (navigationCallbackRef.current) {
              setTimeout(() => navigationCallbackRef.current?.(), 100);
            }
            return { success: true };
          }

          if (!code) {
            await new Promise<void>(resolve => setTimeout(() => resolve(), 600));
            const { data: { session }, error: sessionError } = await supabase.auth.getSession();
            if (sessionError) {
              console.error('❌ Error checking session:', sessionError);
            }
            if (session?.user) {
              const u = session.user;
              const userData: UserData = {
                id: u.id,
                email: u.email || '',
                username: u.user_metadata?.username || u.email?.split('@')[0] || 'user',
                name: u.user_metadata?.name || 'Basketball Player',
                skillLevel: 'beginner',
                position: 'Guard',
                goals: [],
                preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
                createdAt: u.created_at || new Date().toISOString(),
                authProvider: 'supabase',
              };
              setUser(userData);
              setIsLoading(false);
              if (navigationCallbackRef.current) {
                setTimeout(() => navigationCallbackRef.current?.(), 100);
              }
              return { success: true };
            }

            if (__DEV__) {
              console.error(
                '❌ No code in redirect and no session. URL length=',
                url.length,
                'startsWith=',
                url.slice(0, 80),
              );
            }
            console.error('❌ No code found in redirect URL and no existing session');
            return {
              success: false,
              error:
                'Google sign-in did not return a session. Add the printed redirect URI to Supabase (Auth → URL Configuration → Redirect URLs) and try again.',
            };
          }
          
          if (code) {
            
            // CRITICAL: Use the actual redirect URL that was received, not the one we sent
            // Supabase needs the exact redirect URI that was used in the OAuth callback
            // Extract the base redirect URI from the actual URL
            const actualRedirectUri = url.split('?')[0].split('#')[0];
            
            try {
              // Try exchanging code with explicit redirect URI
              // Some Supabase versions require the redirect URI to match exactly
              const exchangePromise = supabase.auth.exchangeCodeForSession(code);
              
              // Add timeout to prevent infinite hanging (increased to 15 seconds)
              const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Code exchange timeout after 15 seconds')), 15000);
              });
              
              // BUG FIX: Properly handle Promise.race rejection — raceError may not be a
              // Supabase response object, so destructuring {data, error} would throw
              let exchangeResult: any;
              try {
                exchangeResult = await Promise.race([
                  exchangePromise,
                  timeoutPromise
                ]);
              } catch (raceError: any) {
                if (raceError?.message?.includes('timeout')) {
                  throw raceError;
                }
                // Wrap non-Supabase errors into the expected shape
                exchangeResult = { data: { session: null }, error: raceError };
              }
              
              const sessionData = exchangeResult?.data ?? { session: null };
              const exchangeError = exchangeResult?.error ?? null;
              
              if (exchangeError) {
                console.error('❌ Code exchange error:', exchangeError);
                console.error('❌ Error code:', exchangeError.code || 'unknown');
                console.error('❌ Error message:', exchangeError.message);
                console.error('❌ Error details:', JSON.stringify(exchangeError, null, 2));
                return { success: false, error: exchangeError.message || 'Failed to complete sign-in' };
              }
              
              if (!sessionData?.session) {
                console.error('❌ Session creation failed - no session in response');
                return { success: false, error: 'Session creation failed' };
              }
              
              // CRITICAL: Force trigger onAuthStateChange by manually calling it
              // Sometimes onAuthStateChange doesn't fire immediately after exchangeCodeForSession
              const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession();
              
              if (sessionError) {
                console.error('❌ Error getting session:', sessionError);
              }
              
              if (currentSession && currentSession.user) {
                // Manually trigger the state update by calling setUser directly
                // This ensures navigation happens even if onAuthStateChange is delayed
                const u = currentSession.user;
                const userData: UserData = {
                  id: u.id,
                  email: u.email || '',
                  username: u.user_metadata?.username || u.email?.split('@')[0] || 'user',
                  name: u.user_metadata?.name || 'Basketball Player',
                  skillLevel: 'beginner',
                  position: 'Guard',
                  goals: [],
                  preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
                  createdAt: u.created_at || new Date().toISOString(),
                  authProvider: 'supabase',
                };
                
                setUser(userData);
                setIsLoading(false);
                
                // Trigger navigation callback immediately
                if (navigationCallbackRef.current) {
                  setTimeout(() => {
                    if (navigationCallbackRef.current) {
                      navigationCallbackRef.current();
                    }
                  }, 100);
                }
                
                // onAuthStateChange will still fire and handle database checks in background
                // But we've already set user state so navigation can happen
              } else {
                console.warn('⚠️ Current session not found after exchange');
                console.warn('⚠️ Session data:', currentSession ? 'exists' : 'null');
                console.warn('⚠️ Using sessionData.session.user instead');
                
                // Fallback: Use sessionData directly
                if (sessionData?.session?.user) {
                  const u = sessionData.session.user;
                  const userData: UserData = {
                    id: u.id,
                    email: u.email || '',
                    username: u.user_metadata?.username || u.email?.split('@')[0] || 'user',
                    name: u.user_metadata?.name || 'Basketball Player',
                    skillLevel: 'beginner',
                    position: 'Guard',
                    goals: [],
                    preferences: { notifications: true, darkMode: true, analytics: true, defaultWorkoutDuration: 30 },
                    createdAt: u.created_at || new Date().toISOString(),
                    authProvider: 'supabase',
                  };
                  
                  setUser(userData);
                  setIsLoading(false);
                  
                  if (navigationCallbackRef.current) {
                    setTimeout(() => {
                      if (navigationCallbackRef.current) {
                        navigationCallbackRef.current();
                      }
                    }, 100);
                  }
                }
              }
              
              return { success: true };
            } catch (error: any) {
              // Catch any exceptions during exchange (network errors, parsing errors, etc.)
              console.error('❌ Exception during code exchange:', error);
              console.error('❌ Exception message:', error?.message);
              console.error('❌ Exception name:', error?.name);
              console.error('❌ Exception stack:', error?.stack);
              
              // Check if it's a timeout
              if (error?.message?.includes('timeout')) {
                console.error('⏱️ Code exchange timed out - this might be a network issue');
                return { 
                  success: false, 
                  error: 'Sign-in timed out. Please check your internet connection and try again.' 
                };
              }
              
              return { 
                success: false, 
                error: error?.message || 'An unexpected error occurred during authentication' 
              };
            }
          }
        } else if (result.type === 'cancel') {
          return { success: false, error: 'Sign-in was canceled' };
        } else if (result.type === 'dismiss') {
          return { success: false, error: 'Sign-in was dismissed' };
        } else {
          console.error('❌ Unknown WebBrowser result type:', result.type);
          return { success: false, error: 'Unknown OAuth result' };
        }
        
        return { success: false, error: 'OAuth flow did not complete' };
      } catch (error: any) {
        console.error('❌ Unexpected OAuth error:', error);
        return { success: false, error: error.message || 'Failed to initiate Google sign-in' };
      }
    };

  const signInWithApple = async (): Promise<{ success: boolean; error?: string }> => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'apple',
      options: {
        redirectTo: 'shootrz://auth/callback',
      },
    });
    if (error) return { success: false, error: error.message };
    return { success: true };
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
    setNavigationCallback,
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
