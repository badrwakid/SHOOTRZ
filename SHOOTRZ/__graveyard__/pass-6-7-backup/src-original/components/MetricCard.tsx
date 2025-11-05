import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME } from '../constants/theme';

interface MetricCardProps {
  title: string;
  value: number;
  maxValue?: number;
  icon: string;
  trend?: 'up' | 'down' | 'stable';
  confidence?: number;
  explanation?: string;
  comparison?: string;
  onPress?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  maxValue = 100,
  icon,
  trend,
  confidence,
  explanation,
  comparison,
  onPress
}) => {
  const getScoreColor = (score: number, max: number) => {
    const percentage = (score / max) * 100;
    if (percentage >= 90) return SHOOTRZ_THEME.colors.success;
    if (percentage >= 80) return SHOOTRZ_THEME.colors.primary;
    if (percentage >= 70) return SHOOTRZ_THEME.colors.warning;
    return SHOOTRZ_THEME.colors.error;
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 90) return SHOOTRZ_THEME.colors.success;
    if (conf >= 70) return SHOOTRZ_THEME.colors.warning;
    return SHOOTRZ_THEME.colors.error;
  };

  const getTrendIcon = (trendType?: string) => {
    switch (trendType) {
      case 'up': return 'trending-up';
      case 'down': return 'trending-down';
      case 'stable': return 'remove';
      default: return 'analytics';
    }
  };

  const getTrendColor = (trendType?: string) => {
    switch (trendType) {
      case 'up': return SHOOTRZ_THEME.colors.success;
      case 'down': return SHOOTRZ_THEME.colors.error;
      case 'stable': return SHOOTRZ_THEME.colors.textSecondary;
      default: return SHOOTRZ_THEME.colors.textSecondary;
    }
  };

  const scoreColor = getScoreColor(value, maxValue);
  const percentage = Math.round((value / maxValue) * 100);

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
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <Ionicons name={icon as any} size={20} color={scoreColor} />
            <Text style={styles.title}>{title}</Text>
          </View>
          {trend && (
            <View style={styles.trendContainer}>
              <Ionicons 
                name={getTrendIcon(trend) as any} 
                size={16} 
                color={getTrendColor(trend)} 
              />
            </View>
          )}
        </View>

        {/* Value Display */}
        <View style={styles.valueContainer}>
          <Text style={[styles.value, { color: scoreColor }]}>
            {value.toFixed(1)}
          </Text>
          <Text style={styles.maxValue}>/ {maxValue}</Text>
          <Text style={[styles.percentage, { color: scoreColor }]}>
            {percentage}%
          </Text>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBackground}>
            <View 
              style={[
                styles.progressFill, 
                { 
                  width: `${percentage}%`,
                  backgroundColor: scoreColor 
                }
              ]} 
            />
          </View>
        </View>

        {/* Confidence Indicator */}
        {confidence !== undefined && (
          <View style={styles.confidenceContainer}>
            <View style={styles.confidenceLabel}>
              <Ionicons 
                name="checkmark-circle" 
                size={12} 
                color={getConfidenceColor(confidence)} 
              />
              <Text style={[styles.confidenceText, { color: getConfidenceColor(confidence) }]}>
                {confidence.toFixed(0)}% confidence
              </Text>
            </View>
          </View>
        )}

        {/* Comparison */}
        {comparison && (
          <View style={styles.comparisonContainer}>
            <Text style={styles.comparisonText}>{comparison}</Text>
          </View>
        )}

        {/* Explanation */}
        {explanation && (
          <View style={styles.explanationContainer}>
            <Text style={styles.explanationText}>{explanation}</Text>
          </View>
        )}

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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.text,
    marginLeft: SHOOTRZ_THEME.spacing.xs,
  },
  trendContainer: {
    padding: 4,
    borderRadius: 4,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  valueContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  value: {
    fontSize: 32,
    fontWeight: '700',
  },
  maxValue: {
    fontSize: 18,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginLeft: 4,
  },
  percentage: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 'auto',
  },
  progressContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  progressBackground: {
    height: 6,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  confidenceContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  confidenceLabel: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  comparisonContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  comparisonText: {
    fontSize: 13,
    color: SHOOTRZ_THEME.colors.primary,
    fontWeight: '500',
  },
  explanationContainer: {
    marginTop: SHOOTRZ_THEME.spacing.xs,
  },
  explanationText: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    lineHeight: 16,
  },
  tapIndicator: {
    position: 'absolute',
    top: SHOOTRZ_THEME.spacing.md,
    right: SHOOTRZ_THEME.spacing.md,
  },
});


