import React, { useState, useEffect, useMemo } from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	TouchableOpacity,
	Switch,
	Alert,
	Modal,
	TextInput,
	ActivityIndicator,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, glass } from '../constants/theme'
import { StatCard } from '../components/StatCard'
import { SectionHeader } from '../components/SectionHeader'
import { PrimaryButton } from '../components/PrimaryButton'
import { SecondaryButton } from '../components/SecondaryButton'
import { useAuth } from '../context/AuthContext'
import { apiService } from '../services/api.service'
import { storageService } from '../services/storage.service'
import { emailService } from '../services/email.service'
import { supabase } from '../services/supabase.client'
import { hapticFeedback } from '../utils/hapticFeedback'

export const ProfileScreen: React.FC = () => {
	const { user, logout, updateProfile } = useAuth()
	const [notifications, setNotifications] = useState(true)
	const [darkMode, setDarkMode] = useState(true)
	const [analytics, setAnalytics] = useState(true)
	const [showEditModal, setShowEditModal] = useState(false)
	const [editName, setEditName] = useState('')
	const [editPosition, setEditPosition] = useState('')
	const [editSkillLevel, setEditSkillLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner')
	const [loading, setLoading] = useState(false)
	const [stats, setStats] = useState({ totalSessions: 0, bestScore: 0, currentStreak: 0, goalsCompleted: 0, totalGoals: 0 })

	useEffect(() => { loadUserStats(); loadPreferences() }, [])

	const loadUserStats = async () => {
		try {
			let serverStats: any = null
			let serverStreak: any = null
			try {
				[serverStats, serverStreak] = await Promise.all([
					apiService.getUserStats(),
					apiService.getUserStreak(),
				])
			} catch { /* fall back to local data */ }

			if (serverStats && (serverStats.totalSessions ?? 0) > 0) {
				const goals = await storageService.getGoals()
				const completed = goals.filter((g: any) => g.completed).length
				setStats({
					totalSessions: serverStats.totalSessions ?? 0,
					bestScore: Math.round(serverStats.bestScore ?? 0),
					currentStreak: serverStreak?.currentStreak ?? 0,
					goalsCompleted: completed,
					totalGoals: goals.length,
				})
			} else {
				const [analysisHistory, goals] = await Promise.all([
					storageService.getAnalysisHistory(),
					storageService.getGoals(),
				])
				const best = analysisHistory.length > 0
					? Math.max(...analysisHistory.map(a => a.scores.total))
					: 0
				const completed = goals.filter((g: any) => g.completed).length
				setStats({
					totalSessions: analysisHistory.length,
					bestScore: best,
					currentStreak: 0,
					goalsCompleted: completed,
					totalGoals: goals.length,
				})
			}

			storageService.migrateToSupabase(apiService).catch(() => {})
		} catch (e) { console.error('Error loading stats:', e) }
	}

	const loadPreferences = async () => {
		try {
			const prefs = await storageService.getPreferences()
			if (prefs) {
				setNotifications(prefs.notifications ?? true)
				setDarkMode(prefs.darkMode ?? true)
				setAnalytics(prefs.analytics ?? true)
			}
		} catch {}
	}

	const savePref = async (key: string, value: boolean) => {
		try {
			const prefs = await storageService.getPreferences() || {}
			await storageService.savePreferences({ ...prefs, [key]: value })
		} catch {}
	}

	const handleNotificationToggle = (v: boolean) => { hapticFeedback.selection(); setNotifications(v); savePref('notifications', v) }
	const handleDarkModeToggle = (v: boolean) => { hapticFeedback.selection(); setDarkMode(v); savePref('darkMode', v); Alert.alert('Theme', 'Dark mode is always on in SHOOTRZ.') }
	const handleAnalyticsToggle = (v: boolean) => { hapticFeedback.selection(); setAnalytics(v); savePref('analytics', v) }

	const handleEditProfile = () => {
		setEditName(user?.name || '')
		setEditPosition(user?.position || '')
		setEditSkillLevel(user?.skillLevel || 'beginner')
		setShowEditModal(true)
	}

	const handleSaveProfile = async () => {
		if (!editName.trim()) { Alert.alert('Error', 'Name is required.'); return }
		setLoading(true)
		try {
			await updateProfile({ name: editName.trim(), position: editPosition, skillLevel: editSkillLevel })
			setShowEditModal(false)
			hapticFeedback.success()
			Alert.alert('Profile Updated', 'Your profile has been saved.')
		} catch { Alert.alert('Error', 'Failed to save profile.') }
		finally { setLoading(false) }
	}

	const handleExportData = async () => {
		if (!user?.email) { Alert.alert('Error', 'Email is required to export data.'); return }
		setLoading(true)
		try {
			const data = await storageService.exportData()
			await emailService.sendDataExportEmail(user.email, data)
			Alert.alert('Export Sent', 'Check your email for the data export.')
		} catch { Alert.alert('Error', 'Failed to export data.') }
		finally { setLoading(false) }
	}

	const handleDeleteAccount = () => {
		Alert.alert(
			'Delete Account',
			'This will permanently delete your account and all data. This cannot be undone.',
			[
				{ text: 'Cancel', style: 'cancel' },
				{
					text: 'Delete',
					style: 'destructive',
					onPress: async () => {
						setLoading(true)
						try {
							const userId = user?.id
							if (userId) {
								void (async () => { try { await supabase.from('videos').delete().eq('user_id', userId) } catch {} })()
								try { await supabase.from('sessions').delete().eq('user_id', userId) } catch {}
								try { await supabase.from('users').delete().eq('id', userId).select() } catch {}
							}
							try { await storageService.clearAllData() } catch {}
							await supabase.auth.signOut()
							await logout()
							Alert.alert('Account Deleted', 'Your account has been removed.')
						} catch (e) { Alert.alert('Error', 'Failed to delete account.') }
						finally { setLoading(false) }
					},
				},
			],
		)
	}

	const handleLogout = () => {
		Alert.alert('Sign Out', 'Are you sure?', [
			{ text: 'Cancel', style: 'cancel' },
			{
				text: 'Sign Out',
				onPress: async () => {
					setLoading(true)
					try { await logout() }
					catch { Alert.alert('Error', 'Failed to sign out.') }
					finally { setLoading(false) }
				},
			},
		])
	}

	const initials = useMemo(() => {
		const n = user?.name || 'P'
		const parts = n.split(' ')
		return parts.length >= 2 ? `${parts[0][0]}${parts[1][0]}`.toUpperCase() : n[0].toUpperCase()
	}, [user?.name])

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			{loading ? (
				<View style={styles.loadingOverlay}>
					<ActivityIndicator size="large" color={colors.brand.orange} />
					<Text style={styles.loadingText}>Processing...</Text>
				</View>
			) : null}

			<ScrollView showsVerticalScrollIndicator={false}>
				{/* Profile Hero */}
				<View style={styles.heroCard}>
					<View style={styles.avatarCircle}>
						<Text style={styles.avatarInitials}>{initials}</Text>
					</View>
					<Text style={styles.userName}>{user?.name || 'Player'}</Text>
					{user?.username ? <Text style={styles.userHandle}>@{user.username}</Text> : null}
					<TouchableOpacity onPress={handleEditProfile} style={styles.editBtn}>
						<Ionicons name="create-outline" size={16} color={colors.brand.orange} />
						<Text style={styles.editText}>Edit Profile</Text>
					</TouchableOpacity>
				</View>

				{/* Stats Row */}
				<View style={styles.statsRow}>
					<StatCard icon="basketball" label="Sessions" value={stats.totalSessions} color="orange" />
					<StatCard icon="trophy" label="Best" value={stats.bestScore} color="default" />
					<StatCard icon="flame" label="Streak" value={stats.currentStreak} color="cyan" />
				</View>

				{/* Preferences */}
				<View style={styles.section}>
					<SectionHeader title="Preferences" />
					<View style={styles.prefRow}>
						<View style={styles.prefLeft}>
							<Ionicons name="notifications-outline" size={20} color={colors.text.secondary} />
							<Text style={styles.prefLabel}>Notifications</Text>
						</View>
						<Switch value={notifications} onValueChange={handleNotificationToggle} trackColor={{ false: colors.bg.elevated, true: colors.brand.orangeDim }} thumbColor={notifications ? colors.brand.orange : colors.text.tertiary} />
					</View>
					<View style={styles.prefRow}>
						<View style={styles.prefLeft}>
							<Ionicons name="moon-outline" size={20} color={colors.text.secondary} />
							<Text style={styles.prefLabel}>Dark Mode</Text>
						</View>
						<Switch value={darkMode} onValueChange={handleDarkModeToggle} trackColor={{ false: colors.bg.elevated, true: colors.brand.orangeDim }} thumbColor={darkMode ? colors.brand.orange : colors.text.tertiary} />
					</View>
					<View style={styles.prefRow}>
						<View style={styles.prefLeft}>
							<Ionicons name="analytics-outline" size={20} color={colors.text.secondary} />
							<Text style={styles.prefLabel}>Analytics</Text>
						</View>
						<Switch value={analytics} onValueChange={handleAnalyticsToggle} trackColor={{ false: colors.bg.elevated, true: colors.brand.orangeDim }} thumbColor={analytics ? colors.brand.orange : colors.text.tertiary} />
					</View>
				</View>

				{/* Account Actions */}
				<View style={styles.section}>
					<SectionHeader title="Account" />
					<TouchableOpacity style={styles.actionRow} onPress={handleExportData}>
						<Ionicons name="download-outline" size={20} color={colors.text.secondary} />
						<Text style={styles.actionLabel}>Export Data</Text>
						<Ionicons name="chevron-forward" size={16} color={colors.text.tertiary} />
					</TouchableOpacity>
					<TouchableOpacity style={styles.actionRow} onPress={handleDeleteAccount}>
						<Ionicons name="trash-outline" size={20} color={colors.error} />
						<Text style={[styles.actionLabel, { color: colors.error }]}>Delete Account</Text>
						<Ionicons name="chevron-forward" size={16} color={colors.text.tertiary} />
					</TouchableOpacity>
				</View>

				{/* Sign Out */}
				<View style={styles.signOutSection}>
					<SecondaryButton
						label="Sign Out"
						onPress={handleLogout}
						variant="danger"
					/>
				</View>

				<View style={{ height: spacing.tabBarHeight }} />
			</ScrollView>

			{/* Edit Profile Modal */}
			<Modal visible={showEditModal} animationType="slide" transparent onRequestClose={() => setShowEditModal(false)}>
				<View style={styles.modalOverlay}>
					<View style={styles.modalCard}>
						<Text style={styles.modalTitle}>Edit Profile</Text>
						<View style={styles.modalField}>
							<Text style={styles.modalLabel}>Name</Text>
							<TextInput
								style={styles.modalInput}
								value={editName}
								onChangeText={setEditName}
								placeholder="Your name"
								placeholderTextColor={colors.text.tertiary}
							/>
						</View>
						<View style={styles.modalField}>
							<Text style={styles.modalLabel}>Position</Text>
							<TextInput
								style={styles.modalInput}
								value={editPosition}
								onChangeText={setEditPosition}
								placeholder="Guard, Forward, Center"
								placeholderTextColor={colors.text.tertiary}
							/>
						</View>
						<View style={styles.modalField}>
							<Text style={styles.modalLabel}>Skill Level</Text>
							<View style={styles.skillPills}>
								{(['beginner', 'intermediate', 'advanced'] as const).map(level => (
									<TouchableOpacity
										key={level}
										style={[styles.skillPill, editSkillLevel === level && styles.skillPillActive]}
										onPress={() => { hapticFeedback.selection(); setEditSkillLevel(level) }}
									>
										<Text style={[styles.skillPillText, editSkillLevel === level && styles.skillPillTextActive]}>
											{level.charAt(0).toUpperCase() + level.slice(1)}
										</Text>
									</TouchableOpacity>
								))}
							</View>
						</View>
						<PrimaryButton label="Save" onPress={handleSaveProfile} loading={loading} fullWidth />
						<TouchableOpacity onPress={() => setShowEditModal(false)} style={styles.modalCancel}>
							<Text style={styles.modalCancelText}>Cancel</Text>
						</TouchableOpacity>
					</View>
				</View>
			</Modal>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: { flex: 1, backgroundColor: colors.bg.primary },
	loadingOverlay: {
		...StyleSheet.absoluteFillObject,
		backgroundColor: 'rgba(8, 10, 14, 0.9)',
		alignItems: 'center',
		justifyContent: 'center',
		zIndex: 10,
	},
	loadingText: { fontSize: typography.size.base, color: colors.text.secondary, marginTop: spacing[3] },
	heroCard: {
		alignItems: 'center',
		paddingVertical: spacing[8],
		paddingHorizontal: spacing.screenPadding,
		backgroundColor: colors.bg.secondary,
		borderBottomWidth: 1,
		borderBottomColor: colors.border.subtle,
	},
	avatarCircle: {
		width: 64,
		height: 64,
		borderRadius: 32,
		backgroundColor: colors.brand.orange,
		alignItems: 'center',
		justifyContent: 'center',
		marginBottom: spacing[3],
	},
	avatarInitials: {
		fontSize: typography.size.xl,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
	},
	userName: {
		fontSize: typography.size.xl,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
	},
	userHandle: {
		fontSize: typography.size.sm,
		color: colors.text.tertiary,
		marginTop: 2,
	},
	editBtn: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[1],
		marginTop: spacing[3],
	},
	editText: {
		fontSize: typography.size.sm,
		color: colors.brand.orange,
		fontWeight: typography.weight.semibold,
	},
	statsRow: {
		flexDirection: 'row',
		gap: spacing[3],
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing[5],
	},
	section: {
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing.sectionGap,
	},
	prefRow: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
		paddingVertical: spacing[3],
		borderBottomWidth: 1,
		borderBottomColor: colors.border.subtle,
	},
	prefLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing[3] },
	prefLabel: { fontSize: typography.size.base, color: colors.text.primary },
	actionRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[3],
		paddingVertical: spacing[3],
		borderBottomWidth: 1,
		borderBottomColor: colors.border.subtle,
	},
	actionLabel: { flex: 1, fontSize: typography.size.base, color: colors.text.primary },
	signOutSection: {
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing[8],
	},
	modalOverlay: {
		flex: 1,
		backgroundColor: 'rgba(8, 10, 14, 0.85)',
		justifyContent: 'center',
		padding: spacing[5],
	},
	modalCard: {
		backgroundColor: colors.bg.elevated,
		borderRadius: radius['2xl'],
		padding: spacing[6],
		borderWidth: 1,
		borderColor: colors.border.default,
	},
	modalTitle: {
		fontSize: typography.size.xl,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
		textAlign: 'center',
		marginBottom: spacing[5],
	},
	modalField: { marginBottom: spacing[4] },
	modalLabel: { fontSize: typography.size.sm, fontWeight: typography.weight.semibold, color: colors.text.secondary, marginBottom: spacing[1] },
	modalInput: {
		backgroundColor: colors.bg.secondary,
		borderWidth: 1,
		borderColor: colors.border.default,
		borderRadius: radius.md,
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
		fontSize: typography.size.base,
		color: colors.text.primary,
	},
	skillPills: { flexDirection: 'row', gap: spacing[2] },
	skillPill: {
		flex: 1,
		paddingVertical: spacing[2],
		borderRadius: radius.pill,
		borderWidth: 1,
		borderColor: colors.border.default,
		alignItems: 'center',
	},
	skillPillActive: { backgroundColor: colors.brand.orangeDim, borderColor: colors.brand.orange },
	skillPillText: { fontSize: typography.size.sm, color: colors.text.secondary },
	skillPillTextActive: { color: colors.brand.orangeLight, fontWeight: typography.weight.bold },
	modalCancel: { alignItems: 'center', paddingVertical: spacing[3], marginTop: spacing[2] },
	modalCancelText: { fontSize: typography.size.sm, color: colors.text.tertiary },
})
