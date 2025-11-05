import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { WORKOUTS } from '../constants/drills';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { storageService } from '../services/storage.service';
import { useAuth } from '../context/AuthContext';
import { EmptyState } from '../components/EmptyState';

export const WorkoutsScreen: React.FC = () => {
  const { user } = useAuth();
  const [activeWorkouts, setActiveWorkouts] = useState<string[]>([]);
  const [workoutStartTimes, setWorkoutStartTimes] = useState<{ [key: string]: Date }>({});

  const handleStartWorkout = async (workoutId: string) => {
    if (activeWorkouts.includes(workoutId)) {
      // Complete workout
      const workout = WORKOUTS.find((w) => w.id === workoutId);
      const startTime = workoutStartTimes[workoutId];
      const duration = startTime ? Math.round((Date.now() - startTime.getTime()) / 60000) : 0;

      Alert.alert('Complete Workout?', `Mark "${workout?.name}" as completed?`, [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Complete',
          onPress: async () => {
            await saveWorkoutSession(workoutId, duration);
            setActiveWorkouts(activeWorkouts.filter((id) => id !== workoutId));
            const newStartTimes = { ...workoutStartTimes };
            delete newStartTimes[workoutId];
            setWorkoutStartTimes(newStartTimes);
            Alert.alert('Success', `${workout?.name} completed! Great work!`);
          },
        },
      ]);
    } else {
      // Start workout
      setActiveWorkouts([...activeWorkouts, workoutId]);
      setWorkoutStartTimes({
        ...workoutStartTimes,
        [workoutId]: new Date(),
      });
    }
  };

  const saveWorkoutSession = async (workoutId: string, duration: number) => {
    try {
      const workout = WORKOUTS.find((w) => w.id === workoutId);
      const session = {
        id: Date.now().toString(),
        userId: user?.id || 'guest',
        workoutId,
        workoutName: workout?.name || '',
        completedAt: new Date().toISOString(),
        duration,
        drillsCompleted: workout?.drills.length || 0,
      };

      await storageService.saveWorkoutSession(session);
    } catch (error) {
      console.error('Error saving workout session:', error);
    }
  };

  const getWorkoutDrills = (workoutId: string) => {
    const workout = WORKOUTS.find((w) => w.id === workoutId);
    return workout ? workout.drills : [];
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.title}>Training Workouts</Text>
          <Text style={styles.subtitle}>Structured programs to improve your game</Text>
        </View>

        {WORKOUTS.map((workout) => (
          <View key={workout.id} style={styles.workoutCard}>
            <View style={styles.workoutHeader}>
              <View style={styles.workoutInfo}>
                <Text style={styles.workoutName}>{workout.name}</Text>
                <Text style={styles.workoutDescription}>{workout.description}</Text>
                <View style={styles.workoutMeta}>
                  <View style={styles.workoutMeta}>
                    <Ionicons name="time" size={14} color={SHOOTRZ_THEME.colors.textSecondary} />
                    <Text style={styles.workoutDuration}>{workout.duration} min</Text>
                  </View>
                  <View style={styles.workoutMeta}>
                    <Ionicons
                      name="basketball"
                      size={14}
                      color={SHOOTRZ_THEME.colors.textSecondary}
                    />
                    <Text style={styles.workoutDrills}>{workout.drills.length} drills</Text>
                  </View>
                </View>
              </View>
              <TouchableOpacity
                style={[
                  styles.startButton,
                  activeWorkouts.includes(workout.id) && styles.activeButton,
                ]}
                onPress={() => handleStartWorkout(workout.id)}
              >
                <Text
                  style={[
                    styles.startButtonText,
                    activeWorkouts.includes(workout.id) && styles.activeButtonText,
                  ]}
                >
                  {activeWorkouts.includes(workout.id) ? 'Complete' : 'Start'}
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.drillsList}>
              <Text style={styles.drillsTitle}>Included Drills:</Text>
              {getWorkoutDrills(workout.id).map((drillId, index) => {
                const drill = WORKOUTS.find((w) => w.drills.includes(drillId));
                return (
                  <View key={index} style={styles.drillItem}>
                    <Text style={styles.drillBullet}>•</Text>
                    <Text style={styles.drillName}>Drill {drillId}</Text>
                  </View>
                );
              })}
            </View>
          </View>
        ))}

        {/* Quick Workout Options */}
        <View style={styles.quickWorkouts}>
          <Text style={styles.sectionTitle}>Quick Workouts</Text>

          <TouchableOpacity
            style={styles.quickWorkoutCard}
            onPress={() => {
              Alert.alert('5-Minute Warm-up', 'Start your warm-up routine now?', [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Start',
                  onPress: () => Alert.alert('Timer Started', 'Your 5-minute warm-up has started!'),
                },
              ]);
            }}
          >
            <Ionicons
              name="flash"
              size={32}
              color={SHOOTRZ_THEME.colors.accent}
              style={{ marginRight: SHOOTRZ_THEME.spacing.md }}
            />
            <View style={styles.quickWorkoutContent}>
              <Text style={styles.quickWorkoutName}>5-Minute Warm-up</Text>
              <Text style={styles.quickWorkoutDescription}>Get ready for practice</Text>
            </View>
            <Text style={styles.quickWorkoutTime}>5 min</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickWorkoutCard}
            onPress={() => {
              Alert.alert('Shooting Session', 'Start your shooting practice now?', [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Start',
                  onPress: () => Alert.alert('Timer Started', 'Your shooting session has started!'),
                },
              ]);
            }}
          >
            <Ionicons
              name="basketball"
              size={32}
              color={SHOOTRZ_THEME.colors.primary}
              style={{ marginRight: SHOOTRZ_THEME.spacing.md }}
            />
            <View style={styles.quickWorkoutContent}>
              <Text style={styles.quickWorkoutName}>Shooting Session</Text>
              <Text style={styles.quickWorkoutDescription}>Focus on shooting form</Text>
            </View>
            <Text style={styles.quickWorkoutTime}>15 min</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickWorkoutCard}
            onPress={() => {
              Alert.alert('Conditioning', 'Start your conditioning workout now?', [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Start',
                  onPress: () =>
                    Alert.alert('Timer Started', 'Your conditioning workout has started!'),
                },
              ]);
            }}
          >
            <Ionicons
              name="barbell"
              size={32}
              color={SHOOTRZ_THEME.colors.secondary}
              style={{ marginRight: SHOOTRZ_THEME.spacing.md }}
            />
            <View style={styles.quickWorkoutContent}>
              <Text style={styles.quickWorkoutName}>Conditioning</Text>
              <Text style={styles.quickWorkoutDescription}>Build endurance and strength</Text>
            </View>
            <Text style={styles.quickWorkoutTime}>20 min</Text>
          </TouchableOpacity>
        </View>
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
  },
  workoutCard: {
    ...COMPONENT_STYLES.card,
    margin: SHOOTRZ_THEME.spacing.md,
  },
  workoutHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  workoutInfo: {
    flex: 1,
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  workoutName: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  workoutDescription: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    lineHeight: 20,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  workoutMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  workoutDuration: {
    ...SHOOTRZ_THEME.typography.caption,
    marginLeft: 4,
  },
  workoutDrills: {
    ...SHOOTRZ_THEME.typography.caption,
    marginLeft: 4,
  },
  startButton: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
  },
  activeButton: {
    backgroundColor: SHOOTRZ_THEME.colors.secondary,
  },
  startButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  activeButtonText: {
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  drillsList: {
    borderTopWidth: 1,
    borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingTop: SHOOTRZ_THEME.spacing.md,
  },
  drillsTitle: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  drillItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  drillBullet: {
    fontSize: 16,
    color: SHOOTRZ_THEME.colors.primary,
    marginRight: SHOOTRZ_THEME.spacing.sm,
  },
  drillName: {
    ...SHOOTRZ_THEME.typography.bodySmall,
  },
  quickWorkouts: {
    padding: SHOOTRZ_THEME.spacing.md,
  },
  sectionTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  quickWorkoutCard: {
    flexDirection: 'row',
    alignItems: 'center',
    ...COMPONENT_STYLES.card,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  quickWorkoutContent: {
    flex: 1,
  },
  quickWorkoutName: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    marginBottom: 2,
  },
  quickWorkoutDescription: {
    ...SHOOTRZ_THEME.typography.bodySmall,
  },
  quickWorkoutTime: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.primary,
  },
});
