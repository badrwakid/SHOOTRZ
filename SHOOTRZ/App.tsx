import { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { AppNavigator } from './src/navigation/AppNavigator';
import { SHOOTRZ_THEME } from './src/constants/theme';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { HistoryProvider } from './src/context/HistoryContext';
import { ProfileProvider } from './src/context/ProfileContext';
import { LoginScreen } from './src/screens/LoginScreen';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { UsernameScreen } from './src/screens/UsernameScreen';
import { SplashScreen } from './src/screens/SplashScreen';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useFonts } from 'expo-font';
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
              setShowUsername(true);
              setShowOnboarding(false);
            } else if (!showOnboarding && !showUsername) {
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

      if (!isAuthenticated) {
        setShowUsername(false);
        setShowOnboarding(false);
      }
    };

    checkUsernameAndShowScreens();
  }, [isAuthenticated, isNewUser, user?.id]);

  const handleLoginSuccess = () => {
    // Login successful - flow will be handled by useEffect
  };

  const handleUsernameComplete = () => {
    setShowUsername(false);
    setShowOnboarding(true);
  };

  const handleOnboardingComplete = () => {
    markOnboardingComplete();
    setShowOnboarding(false);
    setShowUsername(false);
  };

  // Show splash screen first
  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
      </View>
    );
  }

  // Show login if not authenticated (independent check)
  if (!isAuthenticated) {
    // BUG FIX: Removed console.log that printed user ID
    return <LoginScreen onLogin={handleLoginSuccess} />;
  }

  // BUG FIX: Removed console.log that printed user PII (email, ID)

  if (showUsername) {
    return <UsernameScreen onComplete={handleUsernameComplete} />;
  }

  if (showOnboarding) {
    return <OnboardingScreen onComplete={handleOnboardingComplete} />;
  }

  return <AppNavigator />;
}

export default function App() {
  const [fontsLoaded] = useFonts({
    BarlowCondensedBlack: require('./assets/shootrz-design-system/project/fonts/BarlowCondensed-Black.ttf'),
    BarlowCondensedBold: require('./assets/shootrz-design-system/project/fonts/BarlowCondensed-Bold.ttf'),
    DMSansRegular: require('./assets/shootrz-design-system/project/fonts/DMSans-Regular.ttf'),
    DMSansMedium: require('./assets/shootrz-design-system/project/fonts/DMSans-Medium.ttf'),
    DMSansSemiBold: require('./assets/shootrz-design-system/project/fonts/DMSans-SemiBold.ttf'),
    DMSansBold: require('./assets/shootrz-design-system/project/fonts/DMSans-Bold.ttf'),
  });

  if (!fontsLoaded) {
    return null;
  }

  return (
    <SafeAreaProvider>
      <AuthProvider>
        <ProfileProvider>
          <HistoryProvider>
            <StatusBar style="light" backgroundColor={SHOOTRZ_THEME.colors.background} />
            <AppContent />
          </HistoryProvider>
        </ProfileProvider>
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
