import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { getDrillCategoryIcon } from '../utils/iconMapper';

interface DrillCardProps {
  drill: {
    id: string;
    name: string;
    category: string;
    difficulty: string;
    description: string;
    duration: number;
    focusAreas: string[];
  };
  onPress: () => void;
}

export const DrillCard: React.FC<DrillCardProps> = ({ drill, onPress }) => {
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return SHOOTRZ_THEME.colors.secondary;
      case 'intermediate':
        return SHOOTRZ_THEME.colors.primary;
      case 'advanced':
        return SHOOTRZ_THEME.colors.warning;
      default:
        return SHOOTRZ_THEME.colors.textSecondary;
    }
  };

  return (
    <TouchableOpacity style={styles.container} onPress={onPress}>
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Ionicons
            name={getDrillCategoryIcon(drill.category) as any}
            size={24}
            color={SHOOTRZ_THEME.colors.primary}
          />
        </View>
        <View style={styles.titleContainer}>
          <Text style={styles.name}>{drill.name}</Text>
          <Text style={styles.description}>{drill.description}</Text>
        </View>
        <View
          style={[styles.difficulty, { backgroundColor: getDifficultyColor(drill.difficulty) }]}
        >
          <Text style={styles.difficultyText}>{drill.difficulty.toUpperCase()}</Text>
        </View>
      </View>

      <View style={styles.details}>
        <View style={styles.detailItem}>
          <Ionicons name="time" size={14} color={SHOOTRZ_THEME.colors.textSecondary} />
          <Text style={styles.duration}>{drill.duration} min</Text>
        </View>
        <View style={styles.detailItem}>
          <Ionicons name="folder" size={14} color={SHOOTRZ_THEME.colors.textSecondary} />
          <Text style={styles.category}>{drill.category}</Text>
        </View>
      </View>

      <View style={styles.focusAreas}>
        {drill.focusAreas.map((area, index) => (
          <View key={index} style={styles.focusTag}>
            <Text style={styles.focusText}>{area}</Text>
          </View>
        ))}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    ...COMPONENT_STYLES.card,
    marginVertical: SHOOTRZ_THEME.spacing.sm,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  iconContainer: {
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  titleContainer: {
    flex: 1,
  },
  name: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  description: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    lineHeight: 20,
  },
  difficulty: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.sm,
    paddingVertical: SHOOTRZ_THEME.spacing.xs,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
  },
  difficultyText: {
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontSize: 10,
    fontWeight: 'bold',
  },
  details: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  duration: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    marginLeft: 4,
  },
  category: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    textTransform: 'capitalize',
    marginLeft: 4,
  },
  focusAreas: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  focusTag: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingHorizontal: SHOOTRZ_THEME.spacing.sm,
    paddingVertical: SHOOTRZ_THEME.spacing.xs,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    marginRight: SHOOTRZ_THEME.spacing.sm,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.secondary,
  },
  focusText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.secondary,
    fontWeight: '500',
  },
});
