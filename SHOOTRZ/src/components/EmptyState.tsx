import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';

interface EmptyStateProps {
  icon: string;
  title: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  message,
  actionText,
  onAction,
}) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;
  const iconScale = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: SHOOTRZ_THEME.animations.slow,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: SHOOTRZ_THEME.animations.slow,
          useNativeDriver: true,
        }),
      ]),
      Animated.spring(iconScale, {
        toValue: 1,
        tension: 50,
        friction: 5,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      <LinearGradient
        colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
        style={styles.card}
      >
        <Animated.View
          style={[
            styles.iconContainer,
            {
              transform: [{ scale: iconScale }],
            },
          ]}
        >
          <Ionicons name={icon as any} size={64} color={SHOOTRZ_THEME.colors.primary} />
        </Animated.View>

        <Text style={styles.title}>{title}</Text>
        <Text style={styles.message}>{message}</Text>

        {actionText && onAction && (
          <TouchableOpacity style={styles.actionButton} onPress={onAction}>
            <LinearGradient
              colors={SHOOTRZ_THEME.gradients.primary}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.buttonGradient}
            >
              <Text style={styles.actionText}>{actionText}</Text>
            </LinearGradient>
          </TouchableOpacity>
        )}
      </LinearGradient>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.xl,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    padding: SHOOTRZ_THEME.spacing.xxl,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    alignItems: 'center',
  },
  iconContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  title: {
    ...SHOOTRZ_THEME.typography.heading2,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  message: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: SHOOTRZ_THEME.spacing.xl,
  },
  actionButton: {
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    overflow: 'hidden',
  },
  buttonGradient: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.xl,
    paddingVertical: SHOOTRZ_THEME.spacing.md,
  },
  actionText: {
    ...SHOOTRZ_THEME.typography.button,
    textAlign: 'center',
  },
});
