import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME } from '../constants/theme';

interface PlayerComparisonCardProps {
  player: {
    name: string;
    similarity: number;
    position: string;
    style: string;
    best_for: string;
    key_differences: Array<{
      metric: string;
      user_value: number;
      player_value: number;
      difference: number;
      improvement_direction: string;
    }>;
  };
  onPress: () => void;
}

export const PlayerComparisonCard: React.FC<PlayerComparisonCardProps> = ({ 
  player, 
  onPress 
}) => {
  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 80) return SHOOTRZ_THEME.colors.success;
    if (similarity >= 60) return SHOOTRZ_THEME.colors.primary;
    if (similarity >= 40) return SHOOTRZ_THEME.colors.warning;
    return SHOOTRZ_THEME.colors.error;
  };

  const getSimilarityText = (similarity: number) => {
    if (similarity >= 80) return 'Excellent Match';
    if (similarity >= 60) return 'Good Match';
    if (similarity >= 40) return 'Fair Match';
    return 'Needs Work';
  };

  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.8}>
      <LinearGradient
        colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
        style={styles.card}
      >
        {/* Player Header */}
        <View style={styles.header}>
          <View style={styles.playerInfo}>
            <Text style={styles.playerName}>{player.name}</Text>
            <Text style={styles.position}>{player.position}</Text>
          </View>
          <View style={styles.similarityContainer}>
            <View style={[styles.similarityCircle, { borderColor: getSimilarityColor(player.similarity) }]}>
              <Text style={[styles.similarityText, { color: getSimilarityColor(player.similarity) }]}>
                {player.similarity}%
              </Text>
            </View>
            <Text style={styles.similarityLabel}>{getSimilarityText(player.similarity)}</Text>
          </View>
        </View>

        {/* Style Description */}
        <Text style={styles.style}>{player.style}</Text>

        {/* Best For */}
        <View style={styles.bestForContainer}>
          <Ionicons name="star" size={16} color={SHOOTRZ_THEME.colors.primary} />
          <Text style={styles.bestFor}>Best for: {player.best_for}</Text>
        </View>

        {/* Key Differences */}
        {player.key_differences.length > 0 && (
          <View style={styles.differencesContainer}>
            <Text style={styles.differencesTitle}>Key Differences:</Text>
            {player.key_differences.slice(0, 2).map((diff, index) => (
              <View key={index} style={styles.differenceItem}>
                <Text style={styles.differenceMetric}>{diff.metric}</Text>
                <Text style={styles.differenceValue}>
                  You: {diff.user_value.toFixed(1)}° → {player.name}: {diff.player_value.toFixed(1)}°
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Tap to expand indicator */}
        <View style={styles.expandIndicator}>
          <Ionicons name="chevron-forward" size={20} color={SHOOTRZ_THEME.colors.textSecondary} />
        </View>
      </LinearGradient>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    marginHorizontal: SHOOTRZ_THEME.spacing.sm,
    marginVertical: SHOOTRZ_THEME.spacing.xs,
  },
  card: {
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    padding: SHOOTRZ_THEME.spacing.md,
    minWidth: 280,
    maxWidth: 320,
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
    alignItems: 'flex-start',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 18,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.text,
    marginBottom: 2,
  },
  position: {
    fontSize: 14,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontWeight: '500',
  },
  similarityContainer: {
    alignItems: 'center',
  },
  similarityCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 3,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  similarityText: {
    fontSize: 16,
    fontWeight: '700',
  },
  similarityLabel: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
  },
  style: {
    fontSize: 14,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
    lineHeight: 20,
  },
  bestForContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  bestFor: {
    fontSize: 13,
    color: SHOOTRZ_THEME.colors.primary,
    marginLeft: 4,
    fontWeight: '500',
  },
  differencesContainer: {
    marginTop: SHOOTRZ_THEME.spacing.sm,
  },
  differencesTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.text,
    marginBottom: 4,
  },
  differenceItem: {
    marginBottom: 2,
  },
  differenceMetric: {
    fontSize: 12,
    fontWeight: '500',
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  differenceValue: {
    fontSize: 11,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginLeft: 8,
  },
  expandIndicator: {
    position: 'absolute',
    top: SHOOTRZ_THEME.spacing.md,
    right: SHOOTRZ_THEME.spacing.md,
  },
});


