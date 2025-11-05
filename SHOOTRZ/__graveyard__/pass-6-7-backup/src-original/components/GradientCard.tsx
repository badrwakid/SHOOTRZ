import React, { useRef } from 'react';
import { View, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SHOOTRZ_THEME } from '../constants/theme';

interface GradientCardProps {
  children: React.ReactNode;
  gradient?: string[];
  onPress?: () => void;
  style?: any;
  glowColor?: string;
}

export const GradientCard: React.FC<GradientCardProps> = ({
  children,
  gradient = [SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated],
  onPress,
  style,
  glowColor,
}) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.98,
      tension: 300,
      friction: 10,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      tension: 300,
      friction: 10,
      useNativeDriver: true,
    }).start();
  };

  const CardContent = (
    <LinearGradient
      colors={gradient}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.gradient, style]}
    >
      {glowColor && (
        <View style={[styles.glow, { backgroundColor: glowColor, opacity: 0.1 }]} />
      )}
      {children}
    </LinearGradient>
  );

  if (onPress) {
    return (
      <TouchableOpacity
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={0.9}
      >
        <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
          {CardContent}
        </Animated.View>
      </TouchableOpacity>
    );
  }

  return <View>{CardContent}</View>;
};

const styles = StyleSheet.create({
  gradient: {
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    padding: SHOOTRZ_THEME.spacing.lg,
    position: 'relative',
    overflow: 'hidden',
  },
  glow: {
    position: 'absolute',
    top: -50,
    right: -50,
    width: 150,
    height: 150,
    borderRadius: 75,
    blur: 40,
  },
});
