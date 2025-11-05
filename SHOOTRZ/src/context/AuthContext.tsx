import React, { createContext, useState, useContext, useEffect, ReactNode, startTransition } from 'react';
import { storageService, UserData } from '../services/storage.service';
import { emailService } from '../services/email.service';
import { supabase } from '../services/supabase.client';
import { openBrowserAsync } from 'expo-web-browser';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import { Platform } from 'react-native';

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
          console.log('📋 New user detected');
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
        
        console.log(`📋 Checking status: username="${dbUser.username}", hasUsername=${hasUsername}, hasCompletedOnboarding=${hasCompletedOnboarding}`);
        
        // User is new if they haven't completed onboarding
        // If they completed onboarding, they're NOT new (even if username is email-prefix)
        const isNew = !hasCompletedOnboarding;
        setIsNewUser(isNew);
        console.log(`📋 Existing user. Is new: ${isNew}`);
        
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
      const { data } = await supabase.auth.getSession();
      if (data.session?.user) {
        const u = data.session.user;
        const userData = await createUserDataFromSession(u);
        await storageService.saveUserData(userData);
        setUser(userData);
        setIsNewUser(false);
      } else {
        await storageService.clearAllData();
        setUser(null);
      }
      setIsLoading(false);
    };
    
    const sub = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('🔄 Auth state changed:', event);
      
      try {
        if (session?.user) {
          const u = session.user;
          console.log('✅ User authenticated:', u.email);
          
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
          console.log('📝 No session - clearing user state');
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

  const loadUser = async (): Promise<void> => {}

  const login = async (
    emailOrUsername: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔐 Starting login process...');
      console.log('📧 Email/Username:', emailOrUsername);

      // Validate input
      if (!emailOrUsername || !password) {
        return { success: false, error: 'Email/username and password are required' };
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
      console.log('✅ Supabase auth user created:', u.id);
      
      // Step 2: Handle database record creation
      // If database trigger is set up, it will automatically create the record
      // Otherwise, try to insert (only works if no email confirmation or session exists)
      
      if (data.session) {
        // User is immediately logged in (email confirmation disabled)
        console.log('✅ User has active session, creating database record...');
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
          } else {
            console.log('✅ User record exists (created by trigger)');
          }
        } else {
          console.log('✅ User record created in database:', userRecord);
        }
      } else {
        // Email confirmation required - trigger will create record automatically
        console.log('📧 Email confirmation required. Check your email to verify your account.');
        console.log('✅ Database trigger will create user record automatically.');
        
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
        console.log('✅ Signup successful - awaiting email confirmation');
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
      console.log('✅ Signup completed successfully');
      return { success: true };
    } catch (error) {
      console.error('❌ Signup error:', error);
      return { success: false, error: 'Signup failed. Please try again.' };
    }
  };

  const markOnboardingComplete = async () => {
    setIsNewUser(false);
    
    // Also save to database to persist across app restarts
    if (user?.id) {
      try {
        await supabase
          .from('users')
          .update({ has_completed_onboarding: true })
          .eq('id', user.id);
        console.log('✅ Onboarding completion saved to database');
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
      console.log('✅ Local storage cleared');

      await supabase.auth.signOut();

      console.log('✅ Logout completed successfully');
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
      console.log('📝 Updating user profile:', Object.keys(updates));
      
      // Update local state first
      const updatedUser = { ...user, ...updates };
      setUser(updatedUser);
      
      // Update local storage
      await storageService.saveUserData(updatedUser);
      
      // Update database - especially important for username
      const dbUpdates: any = {};
      
      if (updates.username !== undefined) {
        dbUpdates.username = updates.username;
        console.log('📝 Saving username to database:', updates.username);
      }
      if (updates.name !== undefined) {
        dbUpdates.name = updates.name;
      }
      if (updates.skillLevel !== undefined) {
        dbUpdates.skill_level = updates.skillLevel;
      }
      if (updates.position !== undefined) {
        dbUpdates.position = updates.position;
      }
      
      // Only update database if there are fields to update
      if (Object.keys(dbUpdates).length > 0) {
        const { error: dbError } = await supabase
          .from('users')
          .update(dbUpdates)
          .eq('id', user.id);
        
        if (dbError) {
          console.error('❌ Failed to update user in database:', dbError);
          // Don't throw - local update succeeded, database update can retry
        } else {
          console.log('✅ User profile updated in database');
        }
      }
      
      console.log('✅ Profile updated successfully');
    } catch (error: any) {
      console.error('❌ Error updating profile:', error);
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

      // Use Supabase password reset with app deep link
      console.log('🔍 Sending password reset email via Supabase...');
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: 'shootrz://reset-password',
      });

      if (error) {
        console.log('❌ Password reset failed:', error.message);
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

      console.log('✅ Password reset email sent successfully');
      return { success: true };
    } catch (error) {
      console.error('❌ Password reset error:', error);
      return { success: false, error: 'Password reset failed. Please try again.' };
    }
  };

    const signInWithGoogle = async (): Promise<{ success: boolean; error?: string }> => {
      try {
        console.log('🔐 Initiating Google OAuth with Expo AuthSession...');
        
        // Use Expo's redirect URI
        // The proxy is handled automatically by Expo in development
        const redirectUri = AuthSession.makeRedirectUri({
          scheme: 'shootrz',
          path: 'auth/callback',
        });
        
        console.log('📱 Using redirect URI:', redirectUri);
        console.log('📱 Platform:', Platform.OS);
        console.log('📱 Is Dev Mode:', __DEV__);
        
        // Get OAuth URL from Supabase with the redirect URI
        // Add prompt: 'select_account' to force account picker (always ask which account)
        const { data, error } = await supabase.auth.signInWithOAuth({
          provider: 'google',
          options: {
            redirectTo: redirectUri,
            skipBrowserRedirect: false, // Let Supabase handle browser redirect
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
        
        console.log('✅ OAuth URL generated');
        console.log('🔗 OAuth URL (first 150 chars):', data.url.substring(0, 150) + '...');
        
        // Use WebBrowser to handle the OAuth flow
        // This properly handles redirects and returns the result
        WebBrowser.maybeCompleteAuthSession();
        
        // Open the OAuth URL in browser
        const result = await WebBrowser.openAuthSessionAsync(
          data.url,
          redirectUri
        );
        
        console.log('📋 WebBrowser result type:', result.type);
        console.log('📋 WebBrowser result:', JSON.stringify(result, null, 2));
        
        if (result.type === 'success') {
          // Extract the code from the redirect URL
          const url = result.url;
          console.log('✅ Auth success, redirect URL:', url);
          
          // Parse the URL to extract the code
          // The URL will be something like: shootrz://auth/callback?code=xxx
          // OR the proxy URL which we need to handle
          let code: string | null = null;
          
          // Try to extract code from URL (check query params and hash)
          const queryCodeMatch = url.match(/[?&]code=([^&#]+)/);
          const hashCodeMatch = url.match(/#.*[?&]code=([^&#]+)/);
          
          if (queryCodeMatch) {
            code = decodeURIComponent(queryCodeMatch[1]);
            console.log('✅ Extracted code from query params');
          } else if (hashCodeMatch) {
            code = decodeURIComponent(hashCodeMatch[1]);
            console.log('✅ Extracted code from hash');
          } else {
            // If no code in URL, Supabase might have already handled it
            // Check if we have a session
            console.log('⚠️ No code in URL, checking for existing session...');
            const { data: { session }, error: sessionError } = await supabase.auth.getSession();
            if (sessionError) {
              console.error('❌ Error checking session:', sessionError);
            }
            if (session) {
              console.log('✅ Session already exists (Supabase handled it)');
              console.log('✅ User ID:', session.user.id);
              // Manually set user state since session exists
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
            
            console.error('❌ No code found in redirect URL and no existing session');
            return { success: false, error: 'No authentication code received' };
          }
          
          if (code) {
            // Exchange code for session
            console.log('📝 Exchanging code for session...');
            console.log('📋 Code:', code.substring(0, 20) + '...');
            console.log('📋 Full code length:', code.length);
            console.log('📋 Actual redirect URL:', url);
            console.log('📋 Expected redirect URI:', redirectUri);
            
            // CRITICAL: Use the actual redirect URL that was received, not the one we sent
            // Supabase needs the exact redirect URI that was used in the OAuth callback
            // Extract the base redirect URI from the actual URL
            const actualRedirectUri = url.split('?')[0].split('#')[0]; // Get base URL without params
            console.log('📋 Using actual redirect URI for exchange:', actualRedirectUri);
            
            try {
              console.log('🔄 Calling exchangeCodeForSession...');
              console.log('📋 Supabase URL:', process.env.EXPO_PUBLIC_SUPABASE_URL?.substring(0, 50) || 'NOT SET');
              
              // Try exchanging code with explicit redirect URI
              // Some Supabase versions require the redirect URI to match exactly
              const exchangePromise = supabase.auth.exchangeCodeForSession(code);
              
              // Add timeout to prevent infinite hanging (increased to 15 seconds)
              const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Code exchange timeout after 15 seconds')), 15000);
              });
              
              console.log('⏳ Waiting for exchange response...');
              console.log('📋 Checking Supabase URL:', process.env.EXPO_PUBLIC_SUPABASE_URL?.substring(0, 50) || 'NOT SET');
              
              let exchangeResult: any;
              try {
                exchangeResult = await Promise.race([
                  exchangePromise,
                  timeoutPromise
                ]);
              } catch (raceError: any) {
                // Check if it's our timeout or a real error
                if (raceError?.message?.includes('timeout')) {
                  throw raceError;
                }
                // If it's not a timeout, it might be the actual exchange result with an error
                exchangeResult = raceError;
              }
              
              const { data: sessionData, error: exchangeError } = exchangeResult;
              
              console.log('📋 Exchange response received');
              
              if (exchangeError) {
                console.error('❌ Code exchange error:', exchangeError);
                console.error('❌ Error code:', exchangeError.code || 'unknown');
                console.error('❌ Error message:', exchangeError.message);
                console.error('❌ Error details:', JSON.stringify(exchangeError, null, 2));
                return { success: false, error: exchangeError.message || 'Failed to complete sign-in' };
              }
              
              console.log('📋 Session data received:', {
                hasSession: !!sessionData?.session,
                hasUser: !!sessionData?.session?.user,
                userId: sessionData?.session?.user?.id,
                email: sessionData?.session?.user?.email,
              });
              
              if (!sessionData?.session) {
                console.error('❌ Session creation failed - no session in response');
                console.error('❌ Response data:', JSON.stringify(sessionData, null, 2));
                return { success: false, error: 'Session creation failed' };
              }
              
              console.log('✅ Session created successfully!');
              console.log('✅ User ID:', sessionData.session.user.id);
              console.log('✅ User email:', sessionData.session.user.email);
              console.log('✅ Session expires at:', sessionData.session.expires_at);
              
              // CRITICAL: Force trigger onAuthStateChange by manually calling it
              // Sometimes onAuthStateChange doesn't fire immediately after exchangeCodeForSession
              console.log('🔄 Manually triggering auth state change...');
              
              // Get the current session to pass to onAuthStateChange logic
              console.log('📋 Verifying current session...');
              const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession();
              
              if (sessionError) {
                console.error('❌ Error getting session:', sessionError);
              }
              
              if (currentSession && currentSession.user) {
                console.log('✅ Current session verified - user:', currentSession.user.email);
                
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
                
                console.log('📝 Setting user state directly...');
                setUser(userData);
                setIsLoading(false);
                console.log('✅ User state set - isAuthenticated should now be true');
                
                // Trigger navigation callback immediately
                if (navigationCallbackRef.current) {
                  console.log('🚀 Triggering navigation callback immediately');
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
                  
                  console.log('📝 Setting user state from sessionData...');
                  setUser(userData);
                  setIsLoading(false);
                  
                  if (navigationCallbackRef.current) {
                    console.log('🚀 Triggering navigation callback');
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
          console.log('⚠️ User canceled OAuth');
          return { success: false, error: 'Sign-in was canceled' };
        } else if (result.type === 'dismiss') {
          console.log('⚠️ User dismissed OAuth');
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
