import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { getDrillCategoryIcon } from '../utils/iconMapper';
import { Drill } from '../constants/drills';
import { storageService } from '../services/storage.service';

interface DrillDetailScreenProps {
  drill: Drill;
  onClose: () => void;
}

export const DrillDetailScreen: React.FC<DrillDetailScreenProps> = ({ drill, onClose }) => {
  const [completionCount, setCompletionCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);

  useEffect(() => {
    loadCompletionCount();
  }, []);

  const loadCompletionCount = async () => {
    try {
      const count = await storageService.getDrillCompletionCount(drill.id);
      setCompletionCount(count);
    } catch (error) {
      console.error('Error loading completion count:', error);
    }
  };

  const handleMarkCompleted = async () => {
    setIsCompleting(true);
    try {
      await storageService.markDrillCompleted(drill.id);
      setCompletionCount((prev) => prev + 1);

      Alert.alert(
        'Great Job!',
        `You've completed "${drill.name}" ${completionCount + 1} time${completionCount + 1 > 1 ? 's' : ''}!`,
        [{ text: 'Continue Training', onPress: onClose }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to mark drill as completed');
    } finally {
      setIsCompleting(false);
    }
  };

  const getDifficultyColor = () => {
    switch (drill.difficulty) {
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
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={onClose}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Drill Details</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView style={styles.content}>
        {/* Drill Header */}
        <View style={styles.drillHeader}>
          <Ionicons
            name={getDrillCategoryIcon(drill.category) as any}
            size={32}
            color={SHOOTRZ_THEME.colors.primary}
          />
          <Text style={styles.drillName}>{drill.name}</Text>
          <View style={[styles.difficultyBadge, { backgroundColor: getDifficultyColor() }]}>
            <Text style={styles.difficultyText}>{drill.difficulty.toUpperCase()}</Text>
          </View>
        </View>

        {/* Description */}
        <View style={styles.section}>
          <Text style={styles.description}>{drill.description}</Text>
        </View>

        {/* Meta Info */}
        <View style={styles.metaInfo}>
          <View style={styles.metaItem}>
            <Ionicons name="time" size={16} color={SHOOTRZ_THEME.colors.textSecondary} />
            <Text style={styles.metaText}>{drill.duration} minutes</Text>
          </View>
          <View style={styles.metaItem}>
            <Ionicons name="folder" size={16} color={SHOOTRZ_THEME.colors.textSecondary} />
            <Text style={styles.metaText}>{drill.category}</Text>
          </View>
          <View style={styles.metaItem}>
            <Ionicons
              name="checkmark-circle"
              size={16}
              color={SHOOTRZ_THEME.colors.textSecondary}
            />
            <Text style={styles.metaText}>{completionCount} times completed</Text>
          </View>
        </View>

        {/* Instructions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Instructions</Text>
          {drill.instructions.map((instruction, index) => (
            <View key={index} style={styles.instructionItem}>
              <View style={styles.instructionNumber}>
                <Text style={styles.instructionNumberText}>{index + 1}</Text>
              </View>
              <Text style={styles.instructionText}>{instruction}</Text>
            </View>
          ))}
        </View>

        {/* Focus Areas */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Focus Areas</Text>
          <View style={styles.focusAreas}>
            {drill.focusAreas.map((area, index) => (
              <View key={index} style={styles.focusTag}>
                <Text style={styles.focusText}>{area}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Tips */}
        <View style={styles.tipCard}>
          <Text style={styles.tipIcon}>💡</Text>
          <View style={styles.tipContent}>
            <Text style={styles.tipTitle}>Coach's Tip</Text>
            <Text style={styles.tipText}>
              Focus on quality over quantity. Perfect each repetition before moving to the next one.
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* Bottom Action */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[styles.completeButton, isCompleting && styles.completeButtonDisabled]}
          onPress={handleMarkCompleted}
          disabled={isCompleting}
        >
          {isCompleting ? (
            <ActivityIndicator color={SHOOTRZ_THEME.colors.textPrimary} />
          ) : (
            <>
              <Text style={styles.completeButtonText}>Mark as Completed</Text>
              <Text style={styles.completeButtonIcon}>✓</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: SHOOTRZ_THEME.spacing.xl,
    paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
    paddingBottom: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  backButton: {
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
  },
  backButtonText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.primary,
  },
  headerTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
  },
  content: {
    flex: 1,
  },
  drillHeader: {
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.xl,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  drillName: {
    ...SHOOTRZ_THEME.typography.heading2,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  difficultyBadge: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
  },
  difficultyText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: 'bold',
  },
  section: {
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  description: {
    ...SHOOTRZ_THEME.typography.body,
    textAlign: 'center',
    lineHeight: 24,
  },
  metaInfo: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  metaItem: {
    alignItems: 'center',
  },
  metaText: {
    ...SHOOTRZ_THEME.typography.caption,
    textAlign: 'center',
  },
  sectionTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  instructionItem: {
    flexDirection: 'row',
    marginBottom: SHOOTRZ_THEME.spacing.md,
    alignItems: 'flex-start',
  },
  instructionNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: SHOOTRZ_THEME.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  instructionNumberText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: 'bold',
  },
  instructionText: {
    flex: 1,
    ...SHOOTRZ_THEME.typography.body,
    lineHeight: 24,
  },
  focusAreas: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  focusTag: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
    marginRight: SHOOTRZ_THEME.spacing.sm,
    marginBottom: SHOOTRZ_THEME.spacing.sm,
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.secondary,
  },
  focusText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.secondary,
    fontWeight: '500',
  },
  tipCard: {
    flexDirection: 'row',
    ...COMPONENT_STYLES.card,
    margin: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.secondary,
  },
  tipIcon: {
    fontSize: 24,
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  tipContent: {
    flex: 1,
  },
  tipTitle: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: 'bold',
    color: SHOOTRZ_THEME.colors.secondary,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  tipText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    lineHeight: 20,
  },
  bottomBar: {
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderTopWidth: 1,
    borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  completeButton: {
    ...COMPONENT_STYLES.button.primary,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  completeButtonDisabled: {
    opacity: 0.6,
  },
  completeButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    marginRight: SHOOTRZ_THEME.spacing.sm,
  },
  completeButtonIcon: {
    fontSize: 20,
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
});
