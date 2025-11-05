import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { SHOOTRZ_THEME } from '../constants/theme';
import { ShootrzLogo } from '../components/ShootrzLogo';

interface SplashScreenProps {
  onFinish: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    // Animate logo entrance
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();

    // Auto-proceed after 2 seconds
    const timer = setTimeout(() => {
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }).start(() => onFinish());
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        <View style={styles.logoContainer}>
          <ShootrzLogo size="large" showTagline={false} />
        </View>
        <Text style={styles.loadingText}>Loading your training data...</Text>
        <View style={styles.loadingBar}>
          <Animated.View
            style={[
              styles.loadingProgress,
              {
                transform: [
                  {
                    scaleX: fadeAnim,
                  },
                ],
              },
            ]}
          />
        </View>
      </Animated.View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    width: '100%',
    paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
    paddingTop: SHOOTRZ_THEME.spacing.xl,
  },
  logoContainer: {
    width: '100%',
    alignItems: 'center',
    paddingHorizontal: 8,
    marginBottom: SHOOTRZ_THEME.spacing.xl,
  },
  loadingText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginTop: SHOOTRZ_THEME.spacing.xl,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
    textAlign: 'center',
    alignSelf: 'center',
  },
  loadingBar: {
    width: '80%',
    height: 4,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    overflow: 'hidden',
    alignSelf: 'center',
  },
  loadingProgress: {
    height: '100%',
    width: '100%',
    backgroundColor: SHOOTRZ_THEME.colors.primary,
    transformOrigin: 'left',
  },
});
