import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { AppNavigator } from './src/navigation/AppNavigator';
import { SHOOTRZ_THEME } from './src/constants/theme';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { LoginScreen } from './src/screens/LoginScreen';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { UsernameScreen } from './src/screens/UsernameScreen';
import { SplashScreen } from './src/screens/SplashScreen';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useDeepLinks } from './src/hooks/useDeepLinks';
import { supabase } from './src/services/supabase.client';

function AppContent() {
  const { isAuthenticated, isLoading, isNewUser, user, markOnboardingComplete } = useAuth();
  const [showSplash, setShowSplash] = useState(true);
  const [showUsername, setShowUsername] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Handle deep links for OAuth, password reset, email confirmation
  useDeepLinks(() => {
    // Deep link handled - auth state will update automatically
    console.log('✅ Deep link processed');
  });

  useEffect(() => {
    // Check username from database for accurate detection
    const checkUsernameAndShowScreens = async () => {
      if (isAuthenticated && user?.id) {
        try {
          // Fetch username from database (most reliable source)
          const { data: dbUser, error } = await supabase
            .from('users')
            .select('username')
            .eq('id', user.id)
            .single();
          
          if (error && error.code !== 'PGRST116') {
            console.warn('⚠️ Error checking username:', error);
          }
          
          const hasUsername = !!(dbUser?.username && 
                                 dbUser.username.trim() && 
                                 dbUser.username !== 'user' &&
                                 dbUser.username !== user.email?.split('@')[0]);
          
          if (isNewUser) {
            if (!hasUsername) {
              // New user without username - show username screen
              console.log('📱 New user without username - showing username screen');
              setShowUsername(true);
              setShowOnboarding(false);
            } else if (!showOnboarding && !showUsername) {
              // New user with username - show onboarding
              console.log('📱 New user with username - showing onboarding cards');
              setShowOnboarding(true);
              setShowUsername(false);
            }
          } else {
            // Existing user - no username/onboarding screens
            setShowUsername(false);
            setShowOnboarding(false);
          }
        } catch (err: any) {
          console.error('❌ Error checking username:', err);
          // On error, default to showing username screen for new users
          if (isNewUser) {
            setShowUsername(true);
            setShowOnboarding(false);
          }
        }
      }

      // Reset screens when user logs out
      if (!isAuthenticated) {
        console.log('📱 User logged out - hiding screens');
        setShowUsername(false);
        setShowOnboarding(false);
      }
    };

    checkUsernameAndShowScreens();
  }, [isAuthenticated, isNewUser, user?.id]);

  const handleLoginSuccess = () => {
    console.log('✅ Login success callback triggered');
    // Login successful - flow will be handled by useEffect
  };

  const handleUsernameComplete = () => {
    console.log('✅ Username set - proceeding to onboarding');
    setShowUsername(false);
    setShowOnboarding(true);
  };

  const handleOnboardingComplete = () => {
    console.log('✅ Onboarding completed');
    markOnboardingComplete();
    setShowOnboarding(false);
    setShowUsername(false);
  };

  // Show splash screen first
  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  // Show loading during auth check (independent check)
  if (isLoading) {
    console.log('⏳ Showing loading screen - isLoading is true');
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
      </View>
    );
  }

  // Show login if not authenticated (independent check)
  if (!isAuthenticated) {
    console.log('🔒 Showing login screen - isAuthenticated is false');
    console.log('📋 User state:', user ? `ID: ${user.id}` : 'null');
    return <LoginScreen onLogin={handleLoginSuccess} />;
  }

  // User is authenticated - log transition
  console.log('✅ User authenticated - rendering app content');
  console.log('📋 User:', user ? `ID: ${user.id}, Email: ${user.email}, Username: ${user.username || 'none'}` : 'null');

  // Show username screen for new users without username
  if (showUsername) {
    console.log('📱 Showing username screen');
    return <UsernameScreen onComplete={handleUsernameComplete} />;
  }

  // Show onboarding for new users only (after username is set)
  if (showOnboarding) {
    console.log('📱 Showing onboarding screen');
    return <OnboardingScreen onComplete={handleOnboardingComplete} />;
  }

  // Show main app
  console.log('🚀 Rendering main app navigator');
  return <AppNavigator />;
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar style="light" backgroundColor={SHOOTRZ_THEME.colors.background} />
        <AppContent />
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
