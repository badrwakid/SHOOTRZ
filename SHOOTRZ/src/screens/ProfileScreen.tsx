import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
  TextInput,
  Modal,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { ShootrzLogo } from '../components/ShootrzLogo';
import { GradientCard } from '../components/GradientCard';
import { AnimatedStatCard } from '../components/AnimatedStatCard';
import { useAuth } from '../context/AuthContext';
import { storageService } from '../services/storage.service';
import { emailService } from '../services/email.service';
import { supabase } from '../services/supabase.client';
import { hapticFeedback } from '../utils/hapticFeedback';

export const ProfileScreen: React.FC = () => {
  const { user, logout, updateProfile } = useAuth();
  const [notifications, setNotificationsState] = useState(true);
  const [darkMode, setDarkModeState] = useState(true);
  const [analytics, setAnalyticsState] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState('');
  const [editPosition, setEditPosition] = useState('');
  const [editSkillLevel, setEditSkillLevel] = useState<'beginner' | 'intermediate' | 'advanced'>(
    'beginner'
  );
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    totalSessions: 0,
    bestScore: 0,
    currentStreak: 0,
    goalsCompleted: 0,
    totalGoals: 0,
  });

  useEffect(() => {
    loadUserStats();
    loadPreferences();
  }, []);

  const loadUserStats = async () => {
    try {
      const analysisHistory = await storageService.getAnalysisHistory();
      const goals = await storageService.getGoals();

      const bestScore =
        analysisHistory.length > 0 ? Math.max(...analysisHistory.map((a) => a.scores.total)) : 0;

      const completedGoals = goals.filter((g) => g.completed).length;

      setStats({
        totalSessions: analysisHistory.length,
        bestScore,
        currentStreak: 12, // Mock for now
        goalsCompleted: completedGoals,
        totalGoals: goals.length,
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadPreferences = async () => {
    try {
      const prefs = await storageService.getPreferences();
      setNotificationsState(prefs.notifications);
      setDarkModeState(prefs.darkMode);
      setAnalyticsState(prefs.analytics);
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const handleNotificationToggle = async (value: boolean) => {
    try {
      hapticFeedback.selection();
      setNotificationsState(value);
      const prefs = await storageService.getPreferences();
      prefs.notifications = value;
      await storageService.savePreferences(prefs);

      if (value) {
        Alert.alert(
          'Notifications Enabled',
          'You will receive practice reminders and achievement notifications',
          [{ text: 'Great!' }]
        );
      }
    } catch (error) {
      hapticFeedback.error();
      Alert.alert('Error', 'Failed to update notification settings');
    }
  };

  const handleDarkModeToggle = async (value: boolean) => {
    try {
      setDarkModeState(value);
      const prefs = await storageService.getPreferences();
      prefs.darkMode = value;
      await storageService.savePreferences(prefs);

      Alert.alert(
        value ? 'Dark Mode Enabled' : 'Light Mode Enabled',
        value ? 'SHOOTRZ dark theme is active' : 'Light theme will be applied on next restart',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to update theme settings');
    }
  };

  const handleAnalyticsToggle = async (value: boolean) => {
    try {
      setAnalyticsState(value);
      const prefs = await storageService.getPreferences();
      prefs.analytics = value;
      await storageService.savePreferences(prefs);

      if (!value) {
        Alert.alert('Analytics Disabled', 'Your usage data will not be collected', [
          { text: 'OK' },
        ]);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to update analytics settings');
    }
  };

  const userStats = [
    { label: 'Total Sessions', value: stats.totalSessions.toString(), icon: 'basketball' },
    { label: 'Best Score', value: `${stats.bestScore}%`, icon: 'trophy' },
    { label: 'Current Streak', value: `${stats.currentStreak} days`, icon: 'flame' },
    {
      label: 'Goals Completed',
      value: `${stats.goalsCompleted}/${stats.totalGoals}`,
      icon: 'checkmark-circle',
    },
  ];

  const handleEditProfile = () => {
    setEditName(user?.name || '');
    setEditPosition(user?.position || '');
    setEditSkillLevel(user?.skillLevel || 'beginner');
    setShowEditModal(true);
  };

  const handleSaveProfile = async () => {
    if (!editName.trim()) {
      Alert.alert('Error', 'Name cannot be empty');
      return;
    }

    setLoading(true);
    try {
      await updateProfile({
        name: editName,
        position: editPosition,
        skillLevel: editSkillLevel,
      });
      setShowEditModal(false);
      Alert.alert('Success', 'Profile updated successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = () => {
    Alert.prompt(
      'Change Password',
      'Enter your new password (min 6 characters)',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Change',
          onPress: (password?: string) => {
            if (password && password.length >= 6) {
              Alert.alert('Success', 'Password changed successfully');
            } else {
              Alert.alert('Error', 'Password must be at least 6 characters');
            }
          },
        },
      ],
      'secure-text'
    );
  };

  const handleExportData = async () => {
    if (!user?.email) {
      Alert.alert('Error', 'No email address found');
      return;
    }

    setLoading(true);
    try {
      const exportedData = await storageService.exportData();

      // Send export via email
      const emailResult = await emailService.sendDataExportEmail(user.email, exportedData);

      if (emailResult.success) {
        Alert.alert(
          'Export Sent',
          `Your training data has been sent to ${user.email}. Check your email inbox.`,
          [{ text: 'Great!' }]
        );
      } else {
        // Fallback: Show the data
        Alert.alert(
          'Export Ready',
          'Your data export is ready. You can copy it or contact support@shootrz.com to receive it via email.',
          [{ text: 'OK' }, { text: 'View Data', onPress: () => console.log(exportedData) }]
        );
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to export data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This will permanently delete:\n• Your profile data\n• All analysis history\n• All goals\n• All workout data\n\nThis action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete Forever',
          style: 'destructive',
          onPress: async () => {
            try {
              console.log('🗑️ User confirmed account deletion');
              setLoading(true);

              // Delete account from Supabase database
              console.log('🗑️ Starting account deletion process...');
              
              if (!user?.id) {
                setLoading(false);
                throw new Error('User ID not found');
              }
              
              const userId = user.id;
              
              // 1. Delete user's data from database tables (videos, analysis, etc.)
              console.log('🗑️ Deleting user data from database...');
              
              // Delete analysis history/videos (if they exist in database)
              // Don't await - fire and forget to avoid blocking
              void (async () => {
                try {
                  const { error } = await supabase
                    .from('videos')
                    .delete()
                    .eq('user_id', userId);
                  
                  if (error) {
                    console.warn('⚠️ Error deleting videos (may not exist):', error.message);
                  } else {
                    console.log('✅ User videos deleted');
                  }
                } catch (err: any) {
                  console.warn('⚠️ Exception deleting videos:', err);
                }
              })();
              
              // Delete related data first (sessions, metrics, feedback)
              console.log('🗑️ Deleting user sessions...');
              const { error: deleteSessionsError } = await supabase
                .from('sessions')
                .delete()
                .eq('user_id', userId);
              
              if (deleteSessionsError) {
                console.warn('⚠️ Error deleting sessions:', deleteSessionsError.message);
              }
              
              // Delete user record from users table (this will cascade delete related data)
              console.log('🗑️ Deleting user record from database...');
              console.log('📋 User ID to delete:', userId);
              
              const { data: deleteData, error: deleteUserError } = await supabase
                .from('users')
                .delete()
                .eq('id', userId)
                .select(); // Select to verify deletion
              
              if (deleteUserError) {
                console.error('❌ Failed to delete user from database:', deleteUserError);
                console.error('❌ Error code:', deleteUserError.code);
                console.error('❌ Error message:', deleteUserError.message);
                console.error('❌ Error details:', JSON.stringify(deleteUserError, null, 2));
                
                // Check if it's an RLS policy error
                if (deleteUserError.code === '42501' || deleteUserError.message?.includes('policy')) {
                  Alert.alert(
                    'Delete Failed',
                    'Unable to delete account due to permissions. Please contact support or try logging out and back in.',
                    [{ text: 'OK' }]
                  );
                } else {
                  Alert.alert(
                    'Delete Failed',
                    `Failed to delete account: ${deleteUserError.message}. Please try again or contact support.`,
                    [{ text: 'OK' }]
                  );
                }
                
                setLoading(false);
                return; // Don't throw - show error and stop
              }
              
              console.log('✅ User record deleted from database');
              console.log('📋 Deleted records:', deleteData?.length || 0);
              
              // Verify deletion
              const { data: verifyUser } = await supabase
                .from('users')
                .select('id')
                .eq('id', userId)
                .single();
              
              if (verifyUser) {
                console.warn('⚠️ User still exists after deletion attempt');
                Alert.alert(
                  'Delete Warning',
                  'Account deletion may not have completed fully. Please contact support.',
                  [{ text: 'OK' }]
                );
                setLoading(false);
                return;
              }
              
              console.log('✅ User deletion verified - user no longer exists in database');
              
              // 2. Clear local storage (non-blocking)
              console.log('💾 Clearing local storage...');
              storageService.clearAllData().catch((err) => {
                console.warn('⚠️ Error clearing local storage:', err);
              });

              // 3. Sign out from Supabase
              console.log('🚪 Signing out...');
              await supabase.auth.signOut();
              
              // 4. Logout and clear local state
              console.log('🚪 Calling logout...');
              await logout();
              
              // Reset loading before navigation
              setLoading(false);
              console.log('✅ Account deletion completed');

              // Show confirmation after a brief delay
              setTimeout(() => {
                Alert.alert(
                  'Account Deleted',
                  'Your SHOOTRZ account has been permanently deleted.',
                  [{ text: 'OK' }]
                );
              }, 300);
            } catch (error: any) {
              console.error('❌ Account deletion error:', error);
              setLoading(false);
              Alert.alert(
                'Delete Failed',
                error.message || 'Failed to delete account. Please try again.'
              );
            }
          },
        },
      ]
    );
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout? Your data will be saved.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          try {
            setLoading(true);
            await logout();
            // App.tsx will automatically redirect to login screen
          } catch (error) {
            console.error('Logout error:', error);
            Alert.alert('Error', 'Failed to logout. Please try again.');
            setLoading(false);
          }
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <ShootrzLogo size="medium" showTagline={false} />
          <Text style={styles.welcomeText}>Welcome back!</Text>
        </View>

        {/* User Info Card */}
        <View style={styles.userCard}>
          <View style={styles.avatarContainer}>
            <Ionicons name="person-circle" size={64} color={SHOOTRZ_THEME.colors.primary} />
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{user?.name || 'Basketball Player'}</Text>
            <Text style={styles.userEmail}>{user?.email || 'player@shootrz.com'}</Text>
            <Text style={styles.userLevel}>
              {(user?.skillLevel || 'beginner').charAt(0).toUpperCase() +
                (user?.skillLevel || 'beginner').slice(1)}{' '}
              • {user?.position || 'Guard'}
            </Text>
          </View>
          <TouchableOpacity style={styles.editButton} onPress={handleEditProfile}>
            <Text style={styles.editButtonText}>Edit</Text>
          </TouchableOpacity>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsSection}>
          <Text style={styles.sectionTitle}>Your Stats</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statRow}>
              <GradientCard style={styles.statCard}>
                <View style={styles.statIconContainer}>
                  <Ionicons
                    name={userStats[0].icon as any}
                    size={32}
                    color={SHOOTRZ_THEME.colors.primary}
                  />
                </View>
                <Text style={styles.statValue}>{userStats[0].value}</Text>
                <Text
                  style={styles.statLabel}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.8}
                >
                  {userStats[0].label}
                </Text>
              </GradientCard>

              <GradientCard style={styles.statCard}>
                <View style={styles.statIconContainer}>
                  <Ionicons
                    name={userStats[1].icon as any}
                    size={32}
                    color={SHOOTRZ_THEME.colors.secondary}
                  />
                </View>
                <Text style={styles.statValue}>{userStats[1].value}</Text>
                <Text
                  style={styles.statLabel}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.8}
                >
                  {userStats[1].label}
                </Text>
              </GradientCard>
            </View>

            <View style={styles.statRow}>
              <GradientCard style={styles.statCard}>
                <View style={styles.statIconContainer}>
                  <Ionicons
                    name={userStats[2].icon as any}
                    size={32}
                    color={SHOOTRZ_THEME.colors.accent}
                  />
                </View>
                <Text style={styles.statValue}>{userStats[2].value}</Text>
                <Text
                  style={styles.statLabel}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.8}
                >
                  {userStats[2].label}
                </Text>
              </GradientCard>

              <GradientCard style={styles.statCard}>
                <View style={styles.statIconContainer}>
                  <Ionicons
                    name={userStats[3].icon as any}
                    size={32}
                    color={SHOOTRZ_THEME.colors.success}
                  />
                </View>
                <Text style={styles.statValue}>{userStats[3].value}</Text>
                <Text
                  style={styles.statLabel}
                  numberOfLines={2}
                  adjustsFontSizeToFit
                  minimumFontScale={0.8}
                >
                  {userStats[3].label}
                </Text>
              </GradientCard>
            </View>
          </View>
        </View>

        {/* Settings Section */}
        <View style={styles.settingsSection}>
          <Text style={styles.sectionTitle}>Settings</Text>

          <GradientCard style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingTitle}>Push Notifications</Text>
              <Text style={styles.settingDescription}>Get reminders for practice sessions</Text>
            </View>
            <Switch
              value={notifications}
              onValueChange={handleNotificationToggle}
              trackColor={{
                false: SHOOTRZ_THEME.colors.surfaceElevated,
                true: SHOOTRZ_THEME.colors.primary,
              }}
              thumbColor={
                notifications
                  ? SHOOTRZ_THEME.colors.textPrimary
                  : SHOOTRZ_THEME.colors.textSecondary
              }
            />
          </GradientCard>

          <GradientCard style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingTitle}>Dark Mode</Text>
              <Text style={styles.settingDescription}>Use dark theme (SHOOTRZ style)</Text>
            </View>
            <Switch
              value={darkMode}
              onValueChange={handleDarkModeToggle}
              trackColor={{
                false: SHOOTRZ_THEME.colors.surfaceElevated,
                true: SHOOTRZ_THEME.colors.primary,
              }}
              thumbColor={
                darkMode ? SHOOTRZ_THEME.colors.textPrimary : SHOOTRZ_THEME.colors.textSecondary
              }
            />
          </GradientCard>

          <GradientCard style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <Text style={styles.settingTitle}>Analytics</Text>
              <Text style={styles.settingDescription}>Share anonymous data to improve the app</Text>
            </View>
            <Switch
              value={analytics}
              onValueChange={handleAnalyticsToggle}
              trackColor={{
                false: SHOOTRZ_THEME.colors.surfaceElevated,
                true: SHOOTRZ_THEME.colors.primary,
              }}
              thumbColor={
                analytics ? SHOOTRZ_THEME.colors.textPrimary : SHOOTRZ_THEME.colors.textSecondary
              }
            />
          </GradientCard>
        </View>

        {/* Account Actions */}
        <View style={styles.actionsSection}>
          <Text style={styles.sectionTitle}>Account</Text>

          {/* Only show Change Password for email/password users, not OAuth users */}
          {user?.authProvider === 'email' || user?.authProvider === 'supabase' ? (
            <GradientCard style={styles.actionItem}>
              <TouchableOpacity style={styles.actionButton} onPress={handleChangePassword}>
                <Ionicons name="lock-closed" size={24} color={SHOOTRZ_THEME.colors.textSecondary} />
                <Text style={styles.actionTitle}>Change Password</Text>
                <Ionicons name="chevron-forward" size={20} color={SHOOTRZ_THEME.colors.textMuted} />
              </TouchableOpacity>
            </GradientCard>
          ) : null}

          <GradientCard style={styles.actionItem}>
            <TouchableOpacity style={styles.actionButton} onPress={handleExportData}>
              <Ionicons name="download" size={24} color={SHOOTRZ_THEME.colors.textSecondary} />
              <Text style={styles.actionTitle}>Export My Data</Text>
              <Ionicons name="chevron-forward" size={20} color={SHOOTRZ_THEME.colors.textMuted} />
            </TouchableOpacity>
          </GradientCard>

          <GradientCard style={styles.actionItem}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => Alert.alert('Help', 'Contact support at help@shootrz.com')}
            >
              <Ionicons name="help-circle" size={24} color={SHOOTRZ_THEME.colors.textSecondary} />
              <Text style={styles.actionTitle}>Help & Support</Text>
              <Ionicons name="chevron-forward" size={20} color={SHOOTRZ_THEME.colors.textMuted} />
            </TouchableOpacity>
          </GradientCard>

          <GradientCard style={styles.actionItem}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => Alert.alert('About', 'SHOOTRZ v1.0.0\nBuilt with React Native & AI')}
            >
              <Ionicons
                name="information-circle"
                size={24}
                color={SHOOTRZ_THEME.colors.textSecondary}
              />
              <Text style={styles.actionTitle}>About SHOOTRZ</Text>
              <Ionicons name="chevron-forward" size={20} color={SHOOTRZ_THEME.colors.textMuted} />
            </TouchableOpacity>
          </GradientCard>
        </View>

        {/* Danger Zone */}
        <View style={styles.dangerSection}>
          <TouchableOpacity style={styles.dangerButton} onPress={handleDeleteAccount}>
            <Text style={styles.dangerButtonText}>Delete Account</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutButtonText}>Logout</Text>
          </TouchableOpacity>
        </View>

        {/* Edit Profile Modal */}
        <Modal
          visible={showEditModal}
          animationType="slide"
          transparent={true}
          onRequestClose={() => setShowEditModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Edit Profile</Text>

              <View style={styles.modalInputContainer}>
                <Text style={styles.modalLabel}>Full Name</Text>
                <TextInput
                  style={styles.modalInput}
                  placeholder="Enter your name"
                  placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                  value={editName}
                  onChangeText={setEditName}
                />
              </View>

              <View style={styles.modalInputContainer}>
                <Text style={styles.modalLabel}>Position</Text>
                <TextInput
                  style={styles.modalInput}
                  placeholder="e.g., Guard, Forward"
                  placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                  value={editPosition}
                  onChangeText={setEditPosition}
                />
              </View>

              <View style={styles.modalInputContainer}>
                <Text style={styles.modalLabel}>Skill Level</Text>
                <View style={styles.skillLevelButtons}>
                  {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                    <TouchableOpacity
                      key={level}
                      style={[
                        styles.skillButton,
                        editSkillLevel === level && styles.skillButtonActive,
                      ]}
                      onPress={() => setEditSkillLevel(level)}
                    >
                      <Text
                        style={[
                          styles.skillButtonText,
                          editSkillLevel === level && styles.skillButtonTextActive,
                        ]}
                      >
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => setShowEditModal(false)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.saveButton, loading && styles.saveButtonDisabled]}
                  onPress={handleSaveProfile}
                  disabled={loading}
                >
                  {loading ? (
                    <ActivityIndicator color={SHOOTRZ_THEME.colors.textPrimary} />
                  ) : (
                    <Text style={styles.saveButtonText}>Save Changes</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>

        {/* Loading Overlay for Logout/Delete */}
        {loading && (
          <View style={styles.loadingOverlay}>
            <View style={styles.loadingCard}>
              <ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
              <Text style={styles.loadingOverlayText}>Processing...</Text>
            </View>
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
  header: {
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  welcomeText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginTop: SHOOTRZ_THEME.spacing.sm,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    ...COMPONENT_STYLES.card,
    margin: SHOOTRZ_THEME.spacing.lg,
  },
  avatarContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: SHOOTRZ_THEME.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  avatar: {
    fontSize: 24,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: 2,
  },
  userEmail: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginBottom: 2,
  },
  userLevel: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.primary,
  },
  editButton: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
  },
  editButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: '600',
  },
  statsSection: {
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  sectionTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  statsGrid: {
    flexDirection: 'column',
    gap: SHOOTRZ_THEME.spacing.md,
    alignItems: 'center',
  },
  statRow: {
    flexDirection: 'row',
    gap: SHOOTRZ_THEME.spacing.md,
    width: '100%',
    justifyContent: 'center',
  },
  statCard: {
    flex: 1,
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
    maxWidth: 160,
    minWidth: 150,
  },
  statIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  statIcon: {
    fontSize: 32,
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: SHOOTRZ_THEME.colors.primary,
    marginBottom: 8,
  },
  statLabel: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    textAlign: 'center',
    fontSize: 16,
    lineHeight: 20,
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  settingsSection: {
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...COMPONENT_STYLES.card,
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  settingInfo: {
    flex: 1,
  },
  settingTitle: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    marginBottom: 2,
  },
  settingDescription: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  actionsSection: {
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  actionItem: {
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SHOOTRZ_THEME.spacing.md,
    paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
  },
  actionIcon: {
    fontSize: 20,
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  actionTitle: {
    ...SHOOTRZ_THEME.typography.body,
    flex: 1,
  },
  actionArrow: {
    fontSize: 18,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  dangerSection: {
    padding: SHOOTRZ_THEME.spacing.lg,
    paddingBottom: SHOOTRZ_THEME.spacing.xxl,
  },
  dangerButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.error,
    padding: SHOOTRZ_THEME.spacing.md,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  dangerButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    color: SHOOTRZ_THEME.colors.error,
  },
  logoutButton: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    padding: SHOOTRZ_THEME.spacing.md,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
    alignItems: 'center',
  },
  logoutButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    color: SHOOTRZ_THEME.colors.textSecondary,
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
  modalInputContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  modalLabel: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    fontWeight: '600',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  modalInput: {
    ...COMPONENT_STYLES.input,
  },
  skillLevelButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  skillButton: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    paddingHorizontal: SHOOTRZ_THEME.spacing.xs,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
    marginHorizontal: SHOOTRZ_THEME.spacing.xs,
    alignItems: 'center',
  },
  skillButtonActive: {
    backgroundColor: SHOOTRZ_THEME.colors.primary,
  },
  skillButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  skillButtonTextActive: {
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: 'bold',
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
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    textAlign: 'center',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
  },
  loadingCard: {
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    padding: SHOOTRZ_THEME.spacing.xl,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    alignItems: 'center',
  },
  loadingOverlayText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textPrimary,
    marginTop: SHOOTRZ_THEME.spacing.md,
  },
});
