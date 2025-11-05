import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME } from '../constants/theme';

interface ImprovementStepProps {
  step: number;
  metric: string;
  current: number;
  target: number;
  impact: string;
  drill: string;
  priority: 'high' | 'medium' | 'low';
  onPress?: () => void;
}

export const ImprovementStep: React.FC<ImprovementStepProps> = ({
  step,
  metric,
  current,
  target,
  impact,
  drill,
  priority,
  onPress
}) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return SHOOTRZ_THEME.colors.error;
      case 'medium': return SHOOTRZ_THEME.colors.warning;
      case 'low': return SHOOTRZ_THEME.colors.success;
      default: return SHOOTRZ_THEME.colors.textSecondary;
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return 'alert-circle';
      case 'medium': return 'time';
      case 'low': return 'checkmark-circle';
      default: return 'ellipse';
    }
  };

  const getImprovementDirection = () => {
    if (current < target) return 'up';
    if (current > target) return 'down';
    return 'stable';
  };

  const getDirectionIcon = () => {
    const direction = getImprovementDirection();
    switch (direction) {
      case 'up': return 'arrow-up';
      case 'down': return 'arrow-down';
      default: return 'remove';
    }
  };

  const getDirectionColor = () => {
    const direction = getImprovementDirection();
    switch (direction) {
      case 'up': return SHOOTRZ_THEME.colors.success;
      case 'down': return SHOOTRZ_THEME.colors.warning;
      default: return SHOOTRZ_THEME.colors.textSecondary;
    }
  };

  const improvementNeeded = Math.abs(target - current);
  const improvementPercentage = Math.round((improvementNeeded / Math.max(current, target)) * 100);

  return (
    <TouchableOpacity 
      style={styles.container} 
      onPress={onPress}
      activeOpacity={onPress ? 0.8 : 1}
    >
      <LinearGradient
        colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
        style={styles.card}
      >
        {/* Step Header */}
        <View style={styles.header}>
          <View style={styles.stepContainer}>
            <View style={[styles.stepNumber, { backgroundColor: getPriorityColor(priority) }]}>
              <Text style={styles.stepNumberText}>{step}</Text>
            </View>
            <View style={styles.stepInfo}>
              <Text style={styles.metric}>{metric}</Text>
              <View style={styles.priorityContainer}>
                <Ionicons 
                  name={getPriorityIcon(priority) as any} 
                  size={14} 
                  color={getPriorityColor(priority)} 
                />
                <Text style={[styles.priorityText, { color: getPriorityColor(priority) }]}>
                  {priority.toUpperCase()} PRIORITY
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Current vs Target */}
        <View style={styles.metricsContainer}>
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Current</Text>
            <Text style={styles.metricValue}>{current.toFixed(1)}°</Text>
          </View>
          
          <View style={styles.directionContainer}>
            <Ionicons 
              name={getDirectionIcon() as any} 
              size={20} 
              color={getDirectionColor()} 
            />
            <Text style={[styles.improvementText, { color: getDirectionColor() }]}>
              {improvementNeeded.toFixed(1)}° {getImprovementDirection() === 'up' ? 'increase' : 'decrease'} needed
            </Text>
          </View>
          
          <View style={styles.metricItem}>
            <Text style={styles.metricLabel}>Target</Text>
            <Text style={styles.metricValue}>{target.toFixed(1)}°</Text>
          </View>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBackground}>
            <View 
              style={[
                styles.progressFill, 
                { 
                  width: `${Math.min(100, (current / target) * 100)}%`,
                  backgroundColor: getDirectionColor()
                }
              ]} 
            />
          </View>
          <Text style={styles.progressText}>
            {Math.round((current / target) * 100)}% of target
          </Text>
        </View>

        {/* Impact */}
        <View style={styles.impactContainer}>
          <Ionicons name="trending-up" size={16} color={SHOOTRZ_THEME.colors.primary} />
          <Text style={styles.impactText}>{impact}</Text>
        </View>

        {/* Drill Recommendation */}
        <View style={styles.drillContainer}>
          <View style={styles.drillHeader}>
            <Ionicons name="fitness" size={16} color={SHOOTRZ_THEME.colors.secondary} />
            <Text style={styles.drillTitle}>Recommended Drill</Text>
          </View>
          <Text style={styles.drillText}>{drill}</Text>
        </View>

        {/* Tap indicator */}
        {onPress && (
          <View style={styles.tapIndicator}>
            <Ionicons name="chevron-forward" size={16} color={SHOOTRZ_THEME.colors.textSecondary} />
          </View>
        )}
      </LinearGradient>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: SHOOTRZ_THEME.spacing.xs,
    marginHorizontal: SHOOTRZ_THEME.spacing.sm,
  },
  card: {
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    padding: SHOOTRZ_THEME.spacing.md,
    shadowColor: SHOOTRZ_THEME.colors.shadow,
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  header: {
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  stepContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SHOOTRZ_THEME.spacing.sm,
  },
  stepNumberText: {
    fontSize: 16,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.surface,
  },
  stepInfo: {
    flex: 1,
  },
  metric: {
    fontSize: 18,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.text,
    marginBottom: 2,
  },
  priorityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.text,
  },
  directionContainer: {
    alignItems: 'center',
    flex: 1,
    marginHorizontal: SHOOTRZ_THEME.spacing.sm,
  },
  improvementText: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 2,
    textAlign: 'center',
  },
  progressContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  progressBackground: {
    height: 6,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
  },
  impactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
    padding: SHOOTRZ_THEME.spacing.sm,
    backgroundColor: SHOOTRZ_THEME.colors.primary + '10',
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
  },
  impactText: {
    fontSize: 14,
    color: SHOOTRZ_THEME.colors.primary,
    fontWeight: '600',
    marginLeft: 6,
    flex: 1,
  },
  drillContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  drillHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  drillTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.text,
    marginLeft: 6,
  },
  drillText: {
    fontSize: 13,
    color: SHOOTRZ_THEME.colors.textSecondary,
    lineHeight: 18,
  },
  tapIndicator: {
    position: 'absolute',
    top: SHOOTRZ_THEME.spacing.md,
    right: SHOOTRZ_THEME.spacing.md,
  },
});


