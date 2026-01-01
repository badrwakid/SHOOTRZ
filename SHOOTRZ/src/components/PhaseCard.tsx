import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME } from '../constants/theme';

interface PhaseCardProps {
  name: string;
  score: number;
  metrics: {
    elbow_angle?: number;
    knee_angle?: number;
    release_angle?: number;
    body_alignment?: number;
    [key: string]: number | undefined;
  };
  feedback: string[];
  videoTimestamp: number;
  onPress: () => void;
}

export const PhaseCard: React.FC<PhaseCardProps> = ({
  name,
  score,
  metrics,
  feedback,
  videoTimestamp,
  onPress,
}) => {
  const getPhaseIcon = (phaseName: string) => {
    const icons = {
      setup: 'play-circle',
      dip: 'arrow-down-circle',
      release: 'arrow-up-circle',
      follow_through: 'checkmark-circle',
    };
    return icons[phaseName.toLowerCase() as keyof typeof icons] || 'ellipse';
  };

  const getPhaseColor = (phaseScore: number) => {
    if (phaseScore >= 90) return SHOOTRZ_THEME.colors.success;
    if (phaseScore >= 80) return SHOOTRZ_THEME.colors.primary;
    if (phaseScore >= 70) return SHOOTRZ_THEME.colors.warning;
    return SHOOTRZ_THEME.colors.error;
  };

  const getScoreText = (phaseScore: number) => {
    if (phaseScore >= 90) return 'Excellent';
    if (phaseScore >= 80) return 'Good';
    if (phaseScore >= 70) return 'Fair';
    return 'Needs Work';
  };

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getKeyMetrics = () => {
    const keyMetrics = [];
    if (metrics.elbow_angle !== undefined) {
      keyMetrics.push({ name: 'Elbow', value: metrics.elbow_angle, unit: '°' });
    }
    if (metrics.knee_angle !== undefined) {
      keyMetrics.push({ name: 'Knee', value: metrics.knee_angle, unit: '°' });
    }
    if (metrics.release_angle !== undefined) {
      keyMetrics.push({ name: 'Release', value: metrics.release_angle, unit: '°' });
    }
    if (metrics.body_alignment !== undefined) {
      keyMetrics.push({ name: 'Alignment', value: metrics.body_alignment, unit: '%' });
    }
    return keyMetrics.slice(0, 3); // Show top 3 metrics
  };

  const phaseColor = getPhaseColor(score);
  const keyMetrics = getKeyMetrics();

  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.8}>
      <LinearGradient
        colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
        style={styles.card}
      >
        {/* Phase Header */}
        <View style={styles.header}>
          <View style={styles.phaseInfo}>
            <Ionicons name={getPhaseIcon(name) as any} size={24} color={phaseColor} />
            <View style={styles.phaseDetails}>
              <Text style={styles.phaseName}>{name.charAt(0).toUpperCase() + name.slice(1)}</Text>
              <Text style={styles.timestamp}>{formatTimestamp(videoTimestamp)}</Text>
            </View>
          </View>
          <View style={styles.scoreContainer}>
            <Text style={[styles.score, { color: phaseColor }]}>{score.toFixed(1)}</Text>
            <Text style={styles.scoreLabel}>{getScoreText(score)}</Text>
          </View>
        </View>

        {/* Key Metrics */}
        {keyMetrics.length > 0 && (
          <View style={styles.metricsContainer}>
            {keyMetrics.map((metric, index) => (
              <View key={index} style={styles.metricItem}>
                <Text style={styles.metricName}>{metric.name}</Text>
                <Text style={styles.metricValue}>
                  {metric.value.toFixed(1)}
                  {metric.unit}
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBackground}>
            <View
              style={[
                styles.progressFill,
                {
                  width: `${score}%`,
                  backgroundColor: phaseColor,
                },
              ]}
            />
          </View>
        </View>

        {/* Feedback */}
        {feedback.length > 0 && (
          <View style={styles.feedbackContainer}>
            <View style={styles.feedbackHeader}>
              <Ionicons name="chatbubble" size={14} color={SHOOTRZ_THEME.colors.textSecondary} />
              <Text style={styles.feedbackTitle}>Feedback</Text>
            </View>
            <Text style={styles.feedbackText} numberOfLines={2}>
              {feedback[0]}
            </Text>
          </View>
        )}

        {/* Tap to jump indicator */}
        <View style={styles.jumpIndicator}>
          <Ionicons name="play" size={16} color={SHOOTRZ_THEME.colors.primary} />
          <Text style={styles.jumpText}>Tap to jump to this phase</Text>
        </View>
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
    shadowColor: '#000000',
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
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  phaseInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  phaseDetails: {
    marginLeft: SHOOTRZ_THEME.spacing.sm,
  },
  phaseName: {
    fontSize: 18,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.textPrimary,
    marginBottom: 2,
  },
  timestamp: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  scoreContainer: {
    alignItems: 'center',
  },
  score: {
    fontSize: 24,
    fontWeight: '700',
  },
  scoreLabel: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginTop: 2,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
  },
  metricItem: {
    alignItems: 'center',
  },
  metricName: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  progressContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.md,
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
  feedbackContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  feedbackHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  feedbackTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginLeft: 4,
  },
  feedbackText: {
    fontSize: 13,
    color: SHOOTRZ_THEME.colors.textPrimary,
    lineHeight: 18,
  },
  jumpIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: SHOOTRZ_THEME.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  jumpText: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.primary,
    marginLeft: 4,
    fontWeight: '500',
  },
});
