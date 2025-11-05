import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME } from '../constants/theme';

interface AnimatedStatCardProps {
  value: number | string;
  label: string;
  icon?: string;
  color?: string;
  delay?: number;
  isPercentage?: boolean;
}

export const AnimatedStatCard: React.FC<AnimatedStatCardProps> = ({
  value,
  label,
  icon,
  color = SHOOTRZ_THEME.colors.primary,
  delay = 0,
  isPercentage = false,
}) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;

  // Convert to safe number
  const numericValue = typeof value === 'number' ? value : parseInt(String(value)) || 0;
  const displayText = String(numericValue) + (isPercentage ? '%' : '');

  useEffect(() => {
    Animated.sequence([
      Animated.delay(delay),
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: SHOOTRZ_THEME.animations.slow,
          useNativeDriver: true,
        }),
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 50,
          friction: 7,
          useNativeDriver: true,
        }),
      ]),
    ]).start();

    // Glow pulsing
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [value, delay]);

  const glowOpacity = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.1, 0.3],
  });

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ scale: scaleAnim }],
        },
      ]}
    >
      <LinearGradient
        colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        {/* Glow effect */}
        <Animated.View
          style={[
            styles.glow,
            {
              backgroundColor: color,
              opacity: glowOpacity,
            },
          ]}
        />

        {icon && (
          <View style={styles.iconContainer}>
            <Ionicons name={icon as any} size={24} color={color} />
          </View>
        )}
        
        <Text style={[styles.value, { color }]}>
          {displayText}
        </Text>
        
        <Text style={styles.label}>{label}</Text>

        {/* Decorative corner */}
        <View style={[styles.corner, { borderColor: color }]} />
      </LinearGradient>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    marginHorizontal: SHOOTRZ_THEME.spacing.xs,
  },
  gradient: {
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    padding: SHOOTRZ_THEME.spacing.lg,
    alignItems: 'center',
    position: 'relative',
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  glow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    borderTopLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
    borderTopRightRadius: SHOOTRZ_THEME.borderRadius.lg,
  },
  iconContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  value: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  label: {
    ...SHOOTRZ_THEME.typography.caption,
    textAlign: 'center',
  },
  corner: {
    position: 'absolute',
    top: SHOOTRZ_THEME.spacing.sm,
    right: SHOOTRZ_THEME.spacing.sm,
    width: 12,
    height: 12,
    borderTopWidth: 2,
    borderRightWidth: 2,
    borderTopRightRadius: 4,
  },
});
