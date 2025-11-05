import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';

interface ScoreCardProps {
  title: string;
  score: number;
  maxScore: number;
  color: string;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({ title, score, maxScore, color }) => {
  const percentage = (score / maxScore) * 100;

  return (
    <View style={[styles.container, { borderLeftColor: color }]}>
      <View style={styles.header}>
        <Text style={styles.title}>{title}</Text>
        <Text style={[styles.score, { color }]}>
          {score}/{maxScore}
        </Text>
      </View>
      <View style={styles.progressBar}>
        <View
          style={[
            styles.progress,
            {
              width: `${percentage}%`,
              backgroundColor: color,
            },
          ]}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...COMPONENT_STYLES.card,
    marginVertical: SHOOTRZ_THEME.spacing.sm,
    borderLeftWidth: 4,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  title: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
  },
  score: {
    ...SHOOTRZ_THEME.typography.heading3,
  },
  progressBar: {
    height: 6,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    overflow: 'hidden',
  },
  progress: {
    height: '100%',
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
  },
});
