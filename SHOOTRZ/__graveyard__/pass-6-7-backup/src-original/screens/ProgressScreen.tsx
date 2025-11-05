import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions, ActivityIndicator, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { AnimatedStatCard } from '../components/AnimatedStatCard';
import { ProgressRing } from '../components/ProgressRing';
import { LoadingBasketball } from '../components/LoadingBasketball';
import { GradientCard } from '../components/GradientCard';
import { EmptyState } from '../components/EmptyState';
import { storageService, AnalysisResult } from '../services/storage.service';

const { width } = Dimensions.get('window');

export const ProgressScreen: React.FC = () => {
  const [weeklyData, setWeeklyData] = useState([
    { day: 'Mon', score: 0, date: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000) },
    { day: 'Tue', score: 0, date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000) },
    { day: 'Wed', score: 0, date: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000) },
    { day: 'Thu', score: 0, date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000) },
    { day: 'Fri', score: 0, date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000) },
    { day: 'Sat', score: 0, date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000) },
    { day: 'Sun', score: 0, date: new Date() },
  ]);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalAnalyses: 0,
    averageScore: 0,
    bestScore: 0,
    practiceStreak: 0,
    improvement: 0,
    consistency: 0,
  });

  useEffect(() => {
    loadProgressData();
  }, []);

  const loadProgressData = async () => {
    try {
      const history = await storageService.getAnalysisHistory();
      setAnalysisHistory(history);

      if (history.length > 0) {
        // Calculate stats
        const totalScore = history.reduce((sum, h) => sum + h.scores.total, 0);
        const avgScore = Math.round(totalScore / history.length);
        const bestScore = Math.max(...history.map(h => h.scores.total));

        // Calculate improvement (compare first half vs second half of data)
        const midpoint = Math.floor(history.length / 2);
        let improvement = 0;
        if (history.length >= 4) {
          const firstHalf = history.slice(0, midpoint);
          const secondHalf = history.slice(midpoint);
          const firstHalfAvg = firstHalf.reduce((sum, h) => sum + h.scores.total, 0) / firstHalf.length;
          const secondHalfAvg = secondHalf.reduce((sum, h) => sum + h.scores.total, 0) / secondHalf.length;
          improvement = Math.round(((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100);
        }

        // Calculate consistency (lower variance = more consistent)
        const variance = history.reduce((sum, h) => {
          const diff = h.scores.total - avgScore;
          return sum + (diff * diff);
        }, 0) / history.length;
        const standardDeviation = Math.sqrt(variance);
        const consistency = Math.round(Math.max(0, 100 - standardDeviation));

        setStats({
          totalAnalyses: history.length,
          averageScore: avgScore,
          bestScore,
          practiceStreak: calculateStreak(history),
          improvement,
          consistency,
        });

        // Update weekly data
        updateWeeklyChart(history);
      }
    } catch (error) {
      console.error('Error loading progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStreak = (history: AnalysisResult[]): number => {
    if (history.length === 0) return 0;
    
    // Sort by date, maost recent first
    const sortedHistory = [...history].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    
    let streak = 0;
    let currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0);
    
    // Check if there's activity today or yesterday
    const mostRecentDate = new Date(sortedHistory[0].timestamp);
    mostRecentDate.setHours(0, 0, 0, 0);
    const daysSinceLastActivity = Math.floor((currentDate.getTime() - mostRecentDate.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysSinceLastActivity > 1) {
      return 0; // Streak broken
    }
    
    // Count consecutive days with activity
    const datesWithActivity = new Set<string>();
    sortedHistory.forEach(h => {
      const date = new Date(h.timestamp);
      date.setHours(0, 0, 0, 0);
      datesWithActivity.add(date.toDateString());
    });
    
    let checkDate = new Date(currentDate);
    while (datesWithActivity.has(checkDate.toDateString())) {
      streak++;
      checkDate.setDate(checkDate.getDate() - 1);
    }
    
    return streak;
  };

  const updateWeeklyChart = (history: AnalysisResult[]) => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const now = new Date();
    const weekData = days.map((day, index) => {
      const date = new Date(Date.now() - (6 - index) * 24 * 60 * 60 * 1000);
      date.setHours(0, 0, 0, 0);
      
      const dayAnalyses = history.filter(h => {
        const analysisDate = new Date(h.timestamp);
        const daysDiff = Math.floor((now.getTime() - analysisDate.getTime()) / (1000 * 60 * 60 * 24));
        return daysDiff === (6 - index); // Last 7 days
      });

      const avgScore = dayAnalyses.length > 0
        ? Math.round(dayAnalyses.reduce((sum, h) => sum + h.scores.total, 0) / dayAnalyses.length)
        : 0;

      return { day, score: avgScore, date };
    });

    setWeeklyData(weekData);
  };

  const monthlyStats = [
    { 
      label: 'Total Analyses', 
      value: stats.totalAnalyses.toString(), 
      change: stats.totalAnalyses > 0 ? `${stats.totalAnalyses} total` : 'Start now', 
      positive: true 
    },
    { 
      label: 'Average Score', 
      value: `${stats.averageScore}%`, 
      change: stats.improvement !== 0 ? `${stats.improvement > 0 ? '+' : ''}${stats.improvement}%` : '--', 
      positive: stats.improvement >= 0 
    },
    { 
      label: 'Best Score', 
      value: `${stats.bestScore}%`, 
      change: stats.bestScore >= 90 ? 'Excellent!' : stats.bestScore >= 80 ? 'Great!' : stats.bestScore >= 70 ? 'Good' : 'Keep going', 
      positive: true 
    },
    { 
      label: 'Practice Streak', 
      value: `${stats.practiceStreak} ${stats.practiceStreak === 1 ? 'day' : 'days'}`, 
      change: stats.practiceStreak >= 7 ? '1 week+' : stats.practiceStreak >= 3 ? 'Building' : stats.practiceStreak > 0 ? 'Started' : '--', 
      positive: true 
    },
  ];

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LoadingBasketball message="Loading your progress..." size="large" />
      </View>
    );
  }

  if (analysisHistory.length === 0) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Your Progress</Text>
          <Text style={styles.subtitle}>Track your improvement over time</Text>
        </View>
        <EmptyState
          icon="stats-chart"
          title="No Data Yet"
          message="Complete your first shot analysis to start tracking your progress!"
          actionText="Analyze Now"
          onAction={() => {}}
        />
      </View>
    );
  }

  // Calculate actual progress from analysis history
  const calculateGoalProgress = () => {
    if (analysisHistory.length === 0) return [];
    
    // Calculate average scores for each metric
    const avgElbow = Math.round(
      analysisHistory.reduce((sum, h) => sum + (h.scores.elbow || 0), 0) / analysisHistory.length * 4
    );
    const avgRelease = Math.round(
      analysisHistory.reduce((sum, h) => sum + (h.scores.release || 0), 0) / analysisHistory.length * 4
    );
    const avgBalance = Math.round(
      analysisHistory.reduce((sum, h) => sum + (h.scores.balance || 0), 0) / analysisHistory.length * 4
    );
    
    return [
      { title: 'Improve Elbow Alignment', progress: avgElbow, target: 100 },
      { title: 'Perfect Release Angle', progress: avgRelease, target: 100 },
      { title: 'Better Balance & Stability', progress: avgBalance, target: 100 },
    ];
  };
  
  const recentGoals = calculateGoalProgress();

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScrollView style={styles.scrollView}>
      <View style={styles.header}>
        <Text style={styles.title}>Your Progress</Text>
        <Text style={styles.subtitle}>Track your improvement over time</Text>
      </View>

      {/* Weekly Chart */}
      <View style={styles.chartSection}>
        <Text style={styles.sectionTitle}>This Week's Performance</Text>
        <View style={styles.chartContainer}>
          {weeklyData.map((data, index) => (
            <View key={index} style={styles.chartBar}>
              <View 
                style={[
                  styles.bar, 
                  { 
                    height: (data.score / 100) * 120,
                    backgroundColor: data.score >= 80 ? SHOOTRZ_THEME.colors.secondary : 
                                   data.score >= 70 ? SHOOTRZ_THEME.colors.primary : SHOOTRZ_THEME.colors.warning
                  }
                ]} 
              />
              <Text style={styles.barLabel}>{data.day}</Text>
              <Text style={styles.barValue}>{data.score}%</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Monthly Stats */}
      <View style={styles.statsSection}>
        <Text style={styles.sectionTitle}>Monthly Overview</Text>
        <View style={styles.statsGrid}>
          {monthlyStats.map((stat, index) => (
            <View key={index} style={styles.statCard}>
              <Text style={styles.statValue}>{stat.value}</Text>
              <Text style={styles.statLabel}>{stat.label}</Text>
              <Text style={[styles.statChange, { color: stat.positive ? '#4CAF50' : '#F44336' }]}>
                {stat.change}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {/* Goals Progress */}
      <View style={styles.goalsSection}>
        <Text style={styles.sectionTitle}>Current Goals</Text>
        {recentGoals.map((goal, index) => (
          <View key={index} style={styles.goalCard}>
            <View style={styles.goalHeader}>
              <Text style={styles.goalTitle}>{goal.title}</Text>
              <Text style={styles.goalProgress}>{goal.progress}%</Text>
            </View>
            <View style={styles.goalProgressBar}>
              <View 
                style={[
                  styles.goalProgressFill, 
                  { width: `${goal.progress}%` }
                ]} 
              />
            </View>
          </View>
        ))}
      </View>

      {/* Achievements */}
      {(stats.bestScore >= 90 || stats.practiceStreak >= 7 || stats.totalAnalyses >= 10) && (
        <View style={styles.achievementsSection}>
          <Text style={styles.sectionTitle}>Recent Achievements</Text>
          
          {stats.bestScore >= 90 && (
            <View style={styles.achievementCard}>
              <View style={styles.achievementIconContainer}>
                <Ionicons name="trophy" size={32} color={SHOOTRZ_THEME.colors.secondary} />
              </View>
              <View style={styles.achievementContent}>
                <Text style={styles.achievementTitle}>Perfect Form</Text>
                <Text style={styles.achievementDescription}>
                  Achieved {stats.bestScore}% score - Outstanding performance!
                </Text>
              </View>
            </View>
          )}
          
          {stats.practiceStreak >= 7 && (
            <View style={styles.achievementCard}>
              <View style={styles.achievementIconContainer}>
                <Ionicons name="flame" size={32} color={SHOOTRZ_THEME.colors.accent} />
              </View>
              <View style={styles.achievementContent}>
                <Text style={styles.achievementTitle}>Consistent Practice</Text>
                <Text style={styles.achievementDescription}>
                  {stats.practiceStreak}-day practice streak - Keep it up!
                </Text>
              </View>
            </View>
          )}
          
          {stats.totalAnalyses >= 10 && (
            <View style={styles.achievementCard}>
              <View style={styles.achievementIconContainer}>
                <Ionicons name="stats-chart" size={32} color={SHOOTRZ_THEME.colors.primary} />
              </View>
              <View style={styles.achievementContent}>
                <Text style={styles.achievementTitle}>Dedicated Athlete</Text>
                <Text style={styles.achievementDescription}>
                  Completed {stats.totalAnalyses} analyses - You're committed to improvement!
                </Text>
              </View>
            </View>
          )}
        </View>
      )}
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
  loadingText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginTop: SHOOTRZ_THEME.spacing.md,
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
  chartSection: {
    ...COMPONENT_STYLES.card,
    margin: SHOOTRZ_THEME.spacing.md,
  },
  sectionTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  chartContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'flex-end',
    height: 160,
  },
  chartBar: {
    alignItems: 'center',
    flex: 1,
  },
  bar: {
    width: 20,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  barLabel: {
    ...SHOOTRZ_THEME.typography.caption,
    marginBottom: 2,
  },
  barValue: {
    fontSize: 10,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: '600',
  },
  statsSection: {
    padding: SHOOTRZ_THEME.spacing.md,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    ...COMPONENT_STYLES.card,
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  statValue: {
    ...SHOOTRZ_THEME.typography.heading2,
    color: SHOOTRZ_THEME.colors.primary,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  statLabel: {
    ...SHOOTRZ_THEME.typography.caption,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  statChange: {
    ...SHOOTRZ_THEME.typography.caption,
    fontWeight: '600',
  },
  goalsSection: {
    padding: SHOOTRZ_THEME.spacing.md,
  },
  goalCard: {
    ...COMPONENT_STYLES.card,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  goalTitle: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
  },
  goalProgress: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: 'bold',
    color: SHOOTRZ_THEME.colors.primary,
  },
  goalProgressBar: {
    height: 6,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    overflow: 'hidden',
  },
  goalProgressFill: {
    height: '100%',
    backgroundColor: SHOOTRZ_THEME.colors.secondary,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
  },
  achievementsSection: {
    padding: SHOOTRZ_THEME.spacing.md,
  },
  achievementCard: {
    flexDirection: 'row',
    ...COMPONENT_STYLES.card,
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  achievementIconContainer: {
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  achievementContent: {
    flex: 1,
  },
  achievementTitle: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    marginBottom: 2,
  },
  achievementDescription: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    lineHeight: 18,
  },
});
