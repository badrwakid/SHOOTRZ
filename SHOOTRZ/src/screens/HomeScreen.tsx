import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { getActivityIcon } from '../utils/iconMapper';
import { ShootrzLogo } from '../components/ShootrzLogo';
import { AnimatedStatCard } from '../components/AnimatedStatCard';
import { GradientCard } from '../components/GradientCard';
import { LoadingBasketball } from '../components/LoadingBasketball';
import { EmptyState } from '../components/EmptyState';
import { useAuth } from '../context/AuthContext';
import { storageService } from '../services/storage.service';
import { hapticFeedback } from '../utils/hapticFeedback';

interface HomeScreenProps {
  navigation: any;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState({
    dayStreak: 0,
    totalAnalyses: 0,
    averageScore: 0,
  });
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  const quickActions = [
    {
      title: 'Analyze Shot',
      icon: 'videocam',
      color: SHOOTRZ_THEME.colors.primary,
      screen: 'Analyze',
    },
    {
      title: 'Browse Drills',
      icon: 'basketball',
      color: SHOOTRZ_THEME.colors.secondary,
      screen: 'Drills',
    },
    {
      title: 'Start Workout',
      icon: 'barbell',
      color: SHOOTRZ_THEME.colors.accent,
      screen: 'Workouts',
    },
    {
      title: 'Chat with Coach J',
      icon: 'chatbubbles',
      color: SHOOTRZ_THEME.colors.primaryLight,
      screen: 'Coach J',
    },
  ];

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Refresh data when user returns to home screen
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      console.log('🏠 Home screen focused, refreshing data...');
      loadDashboardData();
    });

    return unsubscribe;
  }, [navigation]);

  const loadDashboardData = async () => {
    try {
      console.log('📊 Loading dashboard data...');
      const [analysisHistory, workoutHistory, drillCompletions] = await Promise.all([
        storageService.getAnalysisHistory(),
        storageService.getWorkoutHistory(),
        storageService.getDrillCompletions(),
      ]);

      console.log('📈 Analysis history:', analysisHistory.length);
      console.log('💪 Workout history:', workoutHistory.length);
      console.log('🏀 Drill completions:', drillCompletions.length);

      // Calculate stats
      const totalScore = analysisHistory.reduce((sum, a) => sum + a.scores.total, 0);
      const avgScore =
        analysisHistory.length > 0 ? Math.round(totalScore / analysisHistory.length) : 0;

      // Calculate day streak from all activities
      const dayStreak = calculateDayStreak(analysisHistory, workoutHistory, drillCompletions);

      console.log('📊 Calculated stats:', {
        dayStreak,
        totalAnalyses: analysisHistory.length,
        averageScore: avgScore,
      });

      setStats({
        dayStreak,
        totalAnalyses: analysisHistory.length,
        averageScore: avgScore,
      });

      // Build recent activity
      const activities: any[] = [];

      // Add recent analyses
      analysisHistory.slice(0, 2).forEach((analysis) => {
        activities.push({
          type: 'Analysis',
          score: analysis.scores.total,
          date: getRelativeDate(analysis.timestamp),
        });
      });

      // Add recent workouts
      workoutHistory.slice(0, 1).forEach((workout) => {
        activities.push({
          type: 'Workout',
          name: workout.workoutName,
          date: getRelativeDate(workout.completedAt),
        });
      });

      // Add recent drills
      if (drillCompletions.length > 0) {
        const lastDrill = drillCompletions[drillCompletions.length - 1];
        activities.push({
          type: 'Drill',
          name: 'Drill Completed',
          date: getRelativeDate(lastDrill.completedAt),
        });
      }

      setRecentActivity(activities.slice(0, 3));
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateDayStreak = (
    analysisHistory: any[],
    workoutHistory: any[],
    drillCompletions: any[]
  ): number => {
    console.log('🔥 Calculating day streak...');

    // Combine all activities with timestamps
    const allActivities: { date: Date; type: string }[] = [];

    // Add analyses
    analysisHistory.forEach((analysis) => {
      allActivities.push({
        date: new Date(analysis.timestamp),
        type: 'analysis',
      });
    });

    // Add workouts
    workoutHistory.forEach((workout) => {
      allActivities.push({
        date: new Date(workout.completedAt),
        type: 'workout',
      });
    });

    // Add drill completions
    drillCompletions.forEach((drill) => {
      allActivities.push({
        date: new Date(drill.completedAt),
        type: 'drill',
      });
    });

    if (allActivities.length === 0) {
      console.log('❌ No activities found, streak = 0');
      return 0;
    }

    // Sort by date (most recent first)
    allActivities.sort((a, b) => b.date.getTime() - a.date.getTime());

    // Get unique dates (one activity per day counts)
    const uniqueDates = new Set<string>();
    allActivities.forEach((activity) => {
      const dateStr = activity.date.toDateString();
      uniqueDates.add(dateStr);
    });

    const sortedDates = Array.from(uniqueDates).sort(
      (a, b) => new Date(b).getTime() - new Date(a).getTime()
    );

    console.log('📅 Unique activity dates:', sortedDates);

    // Calculate consecutive days from today
    let streak = 0;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 0; i < sortedDates.length; i++) {
      const activityDate = new Date(sortedDates[i]);
      activityDate.setHours(0, 0, 0, 0);

      const daysDiff = Math.floor(
        (today.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24)
      );

      if (daysDiff === i) {
        streak++;
      } else {
        break;
      }
    }

    console.log('🔥 Calculated streak:', streak);
    return streak;
  };

  const getRelativeDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LoadingBasketball message="Loading your training data..." size="large" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={SHOOTRZ_THEME.colors.primary}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <ShootrzLogo size="medium" showTagline={false} />
          </View>
          <View style={styles.headerRight}>
            <Text style={styles.greeting}>Welcome back!</Text>
            <Text style={styles.subtitle}>Ready to improve your game?</Text>
          </View>
        </View>

        {/* Animated Stats Cards */}
        <View style={styles.statsContainer}>
          <AnimatedStatCard
            value={stats.dayStreak}
            label="Day Streak"
            icon="flame"
            color={SHOOTRZ_THEME.colors.primary}
            delay={0}
          />
          <AnimatedStatCard
            value={stats.totalAnalyses}
            label="Analyses"
            icon="basketball"
            color={SHOOTRZ_THEME.colors.secondary}
            delay={100}
          />
          <AnimatedStatCard
            value={stats.averageScore}
            label="Avg Score"
            icon="star"
            color={SHOOTRZ_THEME.colors.accent}
            delay={200}
            isPercentage={true}
          />
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.actionsGrid}>
            <View style={styles.actionRow}>
              <GradientCard
                onPress={() => {
                  hapticFeedback.medium();
                  navigation.navigate(quickActions[0].screen);
                }}
                style={styles.actionCard}
                glowColor={quickActions[0].color}
              >
                <View
                  style={[
                    styles.actionIconContainer,
                    { backgroundColor: quickActions[0].color + '20' },
                  ]}
                >
                  <Ionicons
                    name={quickActions[0].icon as any}
                    size={28}
                    color={quickActions[0].color}
                  />
                </View>
                <Text
                  style={styles.actionTitle}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.85}
                >
                  {quickActions[0].title}
                </Text>
                <View style={[styles.actionAccent, { backgroundColor: quickActions[0].color }]} />
              </GradientCard>
              <GradientCard
                onPress={() => {
                  hapticFeedback.medium();
                  navigation.navigate(quickActions[1].screen);
                }}
                style={styles.actionCard}
                glowColor={quickActions[1].color}
              >
                <View
                  style={[
                    styles.actionIconContainer,
                    { backgroundColor: quickActions[1].color + '20' },
                  ]}
                >
                  <Ionicons
                    name={quickActions[1].icon as any}
                    size={28}
                    color={quickActions[1].color}
                  />
                </View>
                <Text
                  style={styles.actionTitle}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.85}
                >
                  {quickActions[1].title}
                </Text>
                <View style={[styles.actionAccent, { backgroundColor: quickActions[1].color }]} />
              </GradientCard>
            </View>
            <View style={styles.actionRow}>
              <GradientCard
                onPress={() => {
                  hapticFeedback.medium();
                  navigation.navigate(quickActions[2].screen);
                }}
                style={styles.actionCard}
                glowColor={quickActions[2].color}
              >
                <View
                  style={[
                    styles.actionIconContainer,
                    { backgroundColor: quickActions[2].color + '20' },
                  ]}
                >
                  <Ionicons
                    name={quickActions[2].icon as any}
                    size={28}
                    color={quickActions[2].color}
                  />
                </View>
                <Text
                  style={styles.actionTitle}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.85}
                >
                  {quickActions[2].title}
                </Text>
                <View style={[styles.actionAccent, { backgroundColor: quickActions[2].color }]} />
              </GradientCard>
              <GradientCard
                onPress={() => {
                  hapticFeedback.medium();
                  navigation.navigate(quickActions[3].screen);
                }}
                style={styles.actionCard}
                glowColor={quickActions[3].color}
              >
                <View
                  style={[
                    styles.actionIconContainer,
                    { backgroundColor: quickActions[3].color + '20' },
                  ]}
                >
                  <Ionicons
                    name={quickActions[3].icon as any}
                    size={28}
                    color={quickActions[3].color}
                  />
                </View>
                <Text
                  style={styles.actionTitle}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.85}
                >
                  {quickActions[3].title}
                </Text>
                <View style={[styles.actionAccent, { backgroundColor: quickActions[3].color }]} />
              </GradientCard>
            </View>
          </View>
        </View>

        {/* Recent Activity */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          {recentActivity.length === 0 ? (
            <EmptyState
              icon="stats-chart"
              title="No Activity Yet"
              message="Start training to see your activity here!"
              actionText="Analyze a Shot"
              onAction={() => {
                hapticFeedback.light();
                navigation.navigate('Analyze');
              }}
            />
          ) : (
            recentActivity.map((activity, index) => (
              <GradientCard key={index} style={styles.activityItem}>
                <View style={styles.activityIcon}>
                  <Ionicons
                    name={getActivityIcon(activity.type) as any}
                    size={20}
                    color={SHOOTRZ_THEME.colors.primary}
                  />
                </View>
                <View style={styles.activityContent}>
                  <Text style={styles.activityTitle}>
                    {activity.type === 'Analysis'
                      ? `Shot Analysis - ${activity.score}%`
                      : activity.type === 'Drill'
                        ? activity.name
                        : activity.name}
                  </Text>
                  <Text style={styles.activityDate}>{activity.date}</Text>
                </View>
                {activity.score != null && activity.score > 0 ? (
                  <View
                    style={[
                      styles.scoreBadge,
                      {
                        backgroundColor:
                          activity.score >= 80
                            ? '#4CAF50'
                            : activity.score >= 60
                              ? '#FF9800'
                              : '#F44336',
                      },
                    ]}
                  >
                    <Text style={styles.scoreText}>{activity.score}%</Text>
                  </View>
                ) : null}
              </GradientCard>
            ))
          )}
        </View>

        {/* Daily Tip with Gradient */}
        <LinearGradient
          colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.tipCard}
        >
          <View style={styles.tipIconContainer}>
            <Text style={styles.tipIcon}>💡</Text>
          </View>
          <View style={styles.tipContent}>
            <Text style={styles.tipTitle}>Coach's Daily Tip</Text>
            <Text style={styles.tipText}>
              Keep your elbow aligned with the basket and follow through with your shooting hand for
              better accuracy.
            </Text>
          </View>
          <View style={[styles.tipBorder, { borderColor: SHOOTRZ_THEME.colors.secondary }]} />
        </LinearGradient>
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
  loadingContainer: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.xs,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logoContainer: {
    flex: 1.2,
    alignItems: 'flex-start',
    paddingLeft: 8,
  },
  headerRight: {
    flex: 0.8,
    alignItems: 'flex-end',
  },
  greeting: {
    ...SHOOTRZ_THEME.typography.heading3,
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
    textAlign: 'right',
    lineHeight: 18,
  },
  subtitle: {
    ...SHOOTRZ_THEME.typography.caption,
    fontSize: 11,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'right',
    lineHeight: 13,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: SHOOTRZ_THEME.spacing.lg,
    justifyContent: 'space-between',
  },
  section: {
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  sectionTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  actionsGrid: {
    flexDirection: 'column',
    gap: SHOOTRZ_THEME.spacing.md,
    alignItems: 'center',
  },
  actionRow: {
    flexDirection: 'row',
    gap: SHOOTRZ_THEME.spacing.md,
    width: '100%',
    justifyContent: 'center',
  },
  actionCard: {
    flex: 1,
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
    maxWidth: 240,
    minWidth: 160,
  },
  actionIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  actionIcon: {
    fontSize: 32,
  },
  actionTitle: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    textAlign: 'center',
    fontSize: 16,
    lineHeight: 20,
  },
  actionAccent: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 3,
    borderBottomLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
    borderBottomRightRadius: SHOOTRZ_THEME.borderRadius.lg,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  activityIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  activityEmoji: {
    fontSize: 18,
  },
  activityContent: {
    flex: 1,
  },
  activityTitle: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    marginBottom: 2,
  },
  activityDate: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  scoreBadge: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.sm,
    paddingVertical: SHOOTRZ_THEME.spacing.xs,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
  },
  scoreText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: 'bold',
  },
  tipCard: {
    margin: SHOOTRZ_THEME.spacing.lg,
    padding: SHOOTRZ_THEME.spacing.lg,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    position: 'relative',
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  tipIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: SHOOTRZ_THEME.colors.secondary + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  tipIcon: {
    fontSize: 20,
  },
  tipContent: {
    flex: 1,
  },
  tipTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    fontSize: 18,
    color: SHOOTRZ_THEME.colors.secondary,
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  tipText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    lineHeight: 22,
  },
  tipBorder: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    borderTopLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
    borderTopRightRadius: SHOOTRZ_THEME.borderRadius.lg,
    borderTopWidth: 2,
  },
});
