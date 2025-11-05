import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { storageService, Goal } from '../services/storage.service';
import { EmptyState } from '../components/EmptyState';

export const GoalsScreen: React.FC = () => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    target: '',
    unit: '',
    deadline: '',
  });

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const savedGoals = await storageService.getGoals();
      if (savedGoals.length === 0) {
        // Create default goals for demo
        const defaultGoals: Goal[] = [
          {
            id: '1',
            title: 'Improve Elbow Alignment',
            description: 'Achieve consistent 90-degree elbow angle in shooting',
            target: 25,
            current: 18,
            unit: 'points',
            deadline: '2024-12-31',
            completed: false,
            createdAt: '2024-10-01',
          },
          {
            id: '2',
            title: 'Perfect Follow-through',
            description: 'Maintain proper follow-through on every shot',
            target: 100,
            current: 72,
            unit: '%',
            deadline: '2024-11-30',
            completed: false,
            createdAt: '2024-10-01',
          },
          {
            id: '3',
            title: 'Build Practice Streak',
            description: 'Practice shooting form daily',
            target: 30,
            current: 12,
            unit: 'days',
            deadline: '2024-12-15',
            completed: false,
            createdAt: '2024-10-01',
          },
        ];
        await storageService.saveGoals(defaultGoals);
        setGoals(defaultGoals);
      } else {
        setGoals(savedGoals);
      }
    } catch (error) {
      console.error('Error loading goals:', error);
    }
  };

  const handleAddGoal = async () => {
    if (!newGoal.title || !newGoal.target) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    const goal: Goal = {
      id: Date.now().toString(),
      title: newGoal.title,
      description: newGoal.description,
      target: parseInt(newGoal.target),
      current: 0,
      unit: newGoal.unit || 'units',
      deadline:
        newGoal.deadline ||
        new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      completed: false,
      createdAt: new Date().toISOString(),
    };

    try {
      await storageService.addGoal(goal);
      setGoals([...goals, goal]);
      setShowAddModal(false);
      setNewGoal({ title: '', description: '', target: '', unit: '', deadline: '' });
    } catch (error) {
      Alert.alert('Error', 'Failed to add goal');
    }
  };

  const handleUpdateProgress = async (goalId: string, newProgress: number) => {
    try {
      const updatedGoals = goals.map((goal) => {
        if (goal.id === goalId) {
          const updatedGoal = { ...goal, current: newProgress };
          if (newProgress >= goal.target) {
            updatedGoal.completed = true;
            // Show celebration
            setTimeout(() => {
              Alert.alert('🎉 Goal Achieved!', `Congratulations! You've completed: ${goal.title}`, [
                { text: 'Awesome!' },
              ]);
            }, 100);
          }
          return updatedGoal;
        }
        return goal;
      });

      setGoals(updatedGoals);
      await storageService.saveGoals(updatedGoals);
      await storageService.updateGoal(goalId, {
        current: newProgress,
        completed: newProgress >= updatedGoals.find((g) => g.id === goalId)!.target,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to update progress');
    }
  };

  const handleDeleteGoal = async (goalId: string) => {
    Alert.alert('Delete Goal', 'Are you sure you want to delete this goal?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            const updatedGoals = goals.filter((g) => g.id !== goalId);
            setGoals(updatedGoals);
            await storageService.saveGoals(updatedGoals);
          } catch (error) {
            Alert.alert('Error', 'Failed to delete goal');
          }
        },
      },
    ]);
  };

  const getProgressPercentage = (goal: Goal) => {
    return Math.min((goal.current / goal.target) * 100, 100);
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return SHOOTRZ_THEME.colors.secondary;
    if (percentage >= 70) return SHOOTRZ_THEME.colors.primary;
    return SHOOTRZ_THEME.colors.warning;
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.title}>My Goals</Text>
          <Text style={styles.subtitle}>Track your basketball improvement journey</Text>
          <TouchableOpacity style={styles.addButton} onPress={() => setShowAddModal(true)}>
            <Text style={styles.addButtonText}>+ Add Goal</Text>
          </TouchableOpacity>
        </View>

        {/* Goals List */}
        {goals.length === 0 ? (
          <EmptyState
            icon="trophy"
            title="No Goals Yet"
            message="Set your first goal to start tracking your basketball improvement journey!"
            actionText="Add Your First Goal"
            onAction={() => setShowAddModal(true)}
          />
        ) : (
          goals.map((goal) => {
            const progressPercentage = getProgressPercentage(goal);
            const progressColor = getProgressColor(progressPercentage);

            return (
              <View key={goal.id} style={styles.goalCard}>
                <View style={styles.goalHeader}>
                  <View style={styles.goalInfo}>
                    <Text style={styles.goalTitle}>{goal.title}</Text>
                    <Text style={styles.goalDescription}>{goal.description}</Text>
                    <Text style={styles.goalDeadline}>Deadline: {goal.deadline}</Text>
                  </View>
                  <View style={styles.goalProgress}>
                    <Text style={styles.progressText}>
                      {goal.current}/{goal.target} {goal.unit}
                    </Text>
                    <Text style={[styles.progressPercentage, { color: progressColor }]}>
                      {Math.round(progressPercentage)}%
                    </Text>
                  </View>
                </View>

                <View style={styles.progressBarContainer}>
                  <View style={styles.progressBar}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width: `${progressPercentage}%`,
                          backgroundColor: progressColor,
                        },
                      ]}
                    />
                  </View>
                </View>

                {goal.completed && (
                  <View style={styles.completedBadge}>
                    <Text style={styles.completedText}>🎉 Goal Completed!</Text>
                  </View>
                )}

                <View style={styles.goalActions}>
                  <TouchableOpacity
                    style={styles.deleteButton}
                    onPress={() => handleDeleteGoal(goal.id)}
                  >
                    <Text style={styles.deleteButtonText}>Delete</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.updateButton}
                    onPress={() => {
                      Alert.prompt(
                        'Update Progress',
                        `Current: ${goal.current} ${goal.unit}`,
                        [
                          { text: 'Cancel', style: 'cancel' },
                          {
                            text: 'Update',
                            onPress: (text?: any) => {
                              const newProgress = parseInt(text || '0');
                              if (!isNaN(newProgress)) {
                                handleUpdateProgress(goal.id, newProgress);
                              }
                            },
                          },
                        ],
                        'plain-text',
                        goal.current.toString()
                      );
                    }}
                  >
                    <Text style={styles.updateButtonText}>Update Progress</Text>
                  </TouchableOpacity>
                </View>
              </View>
            );
          })
        )}

        {/* Add Goal Modal */}
        <Modal
          visible={showAddModal}
          animationType="slide"
          transparent={true}
          onRequestClose={() => setShowAddModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Add New Goal</Text>

              <TextInput
                style={styles.modalInput}
                placeholder="Goal title"
                placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                value={newGoal.title}
                onChangeText={(text) => setNewGoal({ ...newGoal, title: text })}
              />

              <TextInput
                style={styles.modalInput}
                placeholder="Description (optional)"
                placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                value={newGoal.description}
                onChangeText={(text) => setNewGoal({ ...newGoal, description: text })}
                multiline
              />

              <View style={styles.inputRow}>
                <TextInput
                  style={[styles.modalInput, { flex: 1, marginRight: 8 }]}
                  placeholder="Target"
                  placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                  value={newGoal.target}
                  onChangeText={(text) => setNewGoal({ ...newGoal, target: text })}
                  keyboardType="numeric"
                />
                <TextInput
                  style={[styles.modalInput, { flex: 1, marginLeft: 8 }]}
                  placeholder="Unit (e.g., %, days)"
                  placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                  value={newGoal.unit}
                  onChangeText={(text) => setNewGoal({ ...newGoal, unit: text })}
                />
              </View>

              <TextInput
                style={styles.modalInput}
                placeholder="Deadline (YYYY-MM-DD)"
                placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                value={newGoal.deadline}
                onChangeText={(text) => setNewGoal({ ...newGoal, deadline: text })}
              />

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => setShowAddModal(false)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.saveButton} onPress={handleAddGoal}>
                  <Text style={styles.saveButtonText}>Save Goal</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  title: {
    ...SHOOTRZ_THEME.typography.heading2,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  subtitle: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  addButton: {
    ...COMPONENT_STYLES.button.primary,
    alignSelf: 'flex-start',
  },
  addButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    textAlign: 'center',
  },
  goalCard: {
    ...COMPONENT_STYLES.card,
    margin: SHOOTRZ_THEME.spacing.lg,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  goalInfo: {
    flex: 1,
  },
  goalTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  goalDescription: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  goalDeadline: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textMuted,
  },
  goalProgress: {
    alignItems: 'flex-end',
  },
  progressText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginBottom: 2,
  },
  progressPercentage: {
    ...SHOOTRZ_THEME.typography.heading3,
  },
  progressBarContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  progressBar: {
    height: 8,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
  },
  completedBadge: {
    backgroundColor: SHOOTRZ_THEME.colors.secondary,
    padding: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  completedText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: '600',
  },
  goalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  deleteButton: {
    backgroundColor: 'transparent',
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.error,
  },
  deleteButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.error,
    fontWeight: '600',
  },
  updateButton: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
  },
  updateButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.primary,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  modalContent: {
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    padding: SHOOTRZ_THEME.spacing.lg,
    width: '100%',
    maxWidth: 400,
  },
  modalTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
    textAlign: 'center',
  },
  modalInput: {
    ...COMPONENT_STYLES.input,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  inputRow: {
    flexDirection: 'row',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: SHOOTRZ_THEME.spacing.lg,
  },
  cancelButton: {
    ...COMPONENT_STYLES.button.secondary,
    flex: 1,
    marginRight: SHOOTRZ_THEME.spacing.sm,
  },
  cancelButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
  },
  saveButton: {
    ...COMPONENT_STYLES.button.primary,
    flex: 1,
    marginLeft: SHOOTRZ_THEME.spacing.sm,
  },
  saveButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    textAlign: 'center',
  },
});
