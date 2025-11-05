import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';

interface AnimatedScoreCardProps {
  title: string;
  score: number;
  maxScore: number;
  color: string;
  delay?: number;
}

export const AnimatedScoreCard: React.FC<AnimatedScoreCardProps> = ({ 
  title, 
  score, 
  maxScore, 
  color,
  delay = 0 
}) => {
  // Ensure valid numbers
  const safeScore = isNaN(score) ? 0 : Math.max(0, score);
  const safeMaxScore = isNaN(maxScore) || maxScore <= 0 ? 25 : maxScore;
  
  // Debug logging
  console.log(`AnimatedScoreCard ${title}:`, { 
    originalScore: score, 
    originalMaxScore: maxScore,
    safeScore, 
    safeMaxScore, 
    percentage: Math.round((safeScore / safeMaxScore) * 100) 
  });
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const scoreAnim = useRef(new Animated.Value(0)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;
  const [displayScore, setDisplayScore] = React.useState(0);
  const [displayPercentage, setDisplayPercentage] = React.useState(Math.round((safeScore / safeMaxScore) * 100));
  const [displayProgress, setDisplayProgress] = React.useState(0);

  useEffect(() => {
    // Entrance animation
    Animated.sequence([
      Animated.delay(delay),
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: SHOOTRZ_THEME.animations.slow,
          useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
          toValue: 0,
          tension: 50,
          friction: 7,
          useNativeDriver: true,
        }),
      ]),
    ]).start();

    // Score count-up animation
    const scoreListener = scoreAnim.addListener(({ value }) => {
      const roundedValue = Math.round(value);
      setDisplayScore(roundedValue);
      setDisplayPercentage(Math.round((roundedValue / safeMaxScore) * 100));
    });
    
    // Progress bar animation listener
    const progressListener = progressAnim.addListener(({ value }) => {
      setDisplayProgress(Math.round(value));
    });
    
    // Start both animations simultaneously
    Animated.sequence([
      Animated.delay(delay + 200),
      Animated.timing(scoreAnim, {
        toValue: safeScore,
        duration: SHOOTRZ_THEME.animations.verySlow,
        useNativeDriver: false,
      }),
    ]).start();
    
    // Progress bar animation - synchronized with score animation
    Animated.sequence([
      Animated.delay(delay + 200),
      Animated.timing(progressAnim, {
        toValue: (safeScore / safeMaxScore) * 100,
        duration: SHOOTRZ_THEME.animations.verySlow,
        useNativeDriver: false,
      }),
    ]).start();
    
    // Glow pulsing animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();
    
    return () => {
      scoreAnim.removeListener(scoreListener);
      progressAnim.removeListener(progressListener);
    };
  }, [score, maxScore, delay]);

  const glowOpacity = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.8],
  });

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
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        {/* Glow effect */}
        <Animated.View
          style={[
            styles.glowEffect,
            {
              backgroundColor: color,
              opacity: glowOpacity,
            },
          ]}
        />

        {/* Border accent */}
        <View style={[styles.borderAccent, { backgroundColor: color }]} />

        {/* Content */}
        <View style={styles.header}>
          <Text style={styles.title}>{title}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'baseline' }}>
            <Text style={[styles.score, { color }]}>
              {displayScore}
            </Text>
            <Text style={styles.maxScore}>/{safeMaxScore}</Text>
          </View>
        </View>

        {/* Animated progress bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <Animated.View
              style={[
                styles.progress,
                {
                  width: progressAnim.interpolate({
                    inputRange: [0, 100],
                    outputRange: ['0%', '100%'],
                  }),
                  backgroundColor: color,
                },
              ]}
            />
          </View>
          <Text style={styles.percentage}>
            {displayPercentage}%
          </Text>
        </View>
      </LinearGradient>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    overflow: 'hidden',
  },
  gradient: {
    padding: SHOOTRZ_THEME.spacing.lg,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    position: 'relative',
  },
  glowEffect: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
  },
  borderAccent: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    borderTopLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
    borderBottomLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  title: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
  },
  score: {
    ...SHOOTRZ_THEME.typography.heading2,
    fontWeight: 'bold',
  },
  maxScore: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    overflow: 'hidden',
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  progress: {
    height: '100%',
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
  },
  percentage: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontWeight: '600',
    minWidth: 40,
    textAlign: 'right',
  },
});
