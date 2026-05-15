import React, { useState, useMemo, useRef, useCallback, useEffect } from 'react'
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
import { useFocusEffect } from '@react-navigation/native'
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
import { hapticFeedback } from '../utils/hapticFeedback'
import { useProfile } from '../context/ProfileContext'

export const ProfileScreen: React.FC = () => {
	const { user, logout } = useAuth()
	const {
		profile,
		stats,
		preferences,
		profileLoading,
		statsLoading,
		profileError,
		statsError,
		refresh,
		refreshStats,
		updateProfile,
		updatePreferences,
	} = useProfile()
	const [showEditModal, setShowEditModal] = useState(false)
	const [editName, setEditName] = useState('')
	const [editPosition, setEditPosition] = useState('')
	const [editSkillLevel, setEditSkillLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner')
	const [actionLoading, setActionLoading] = useState(false)
	const [preferenceError, setPreferenceError] = useState<string | null>(null)
	const [preferenceUpdating, setPreferenceUpdating] = useState(false)
	const [actionError, setActionError] = useState<string | null>(null)
	const [networkToastMessage, setNetworkToastMessage] = useState<string | null>(null)
	const preferenceUpdateInFlightRef = useRef(false)
	const toastDismissTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

	const isOfflineOrTimeoutError = useCallback((message: string | null): boolean => {
		if (!message) {
			return false
		}
		const normalized = message.toLowerCase()
		return normalized.includes('no internet')
			|| normalized.includes('network')
			|| normalized.includes('timeout')
			|| normalized.includes('timed out')
			|| normalized.includes('failed to fetch')
	}, [])

	const firstNetworkErrorMessage = useMemo(() => (
		[profileError, statsError, preferenceError, actionError].find(message =>
			isOfflineOrTimeoutError(message || null),
		) || null
	), [actionError, isOfflineOrTimeoutError, preferenceError, profileError, statsError])

	const blockingErrorMessage = useMemo(() => (
		[profileError, statsError, preferenceError, actionError].find(message =>
			Boolean(message) && !isOfflineOrTimeoutError(message || null),
		) || null
	), [actionError, isOfflineOrTimeoutError, preferenceError, profileError, statsError])

	useEffect(() => {
		if (!firstNetworkErrorMessage) {
			return
		}
		setNetworkToastMessage(firstNetworkErrorMessage)
		if (toastDismissTimeoutRef.current) {
			clearTimeout(toastDismissTimeoutRef.current)
		}
		toastDismissTimeoutRef.current = setTimeout(() => {
			setNetworkToastMessage(null)
			toastDismissTimeoutRef.current = null
		}, 3200)
	}, [firstNetworkErrorMessage])

	useEffect(() => () => {
		if (toastDismissTimeoutRef.current) {
			clearTimeout(toastDismissTimeoutRef.current)
		}
	}, [])

	useFocusEffect(
		useCallback(() => {
			void refreshStats()
		}, [refreshStats]),
	)

	const updatePreference = async (
		key: 'notifications_enabled' | 'dark_mode_enabled' | 'analytics_enabled',
		value: boolean,
	) => {
		if (preferenceUpdateInFlightRef.current) {
			return
		}

		preferenceUpdateInFlightRef.current = true
		setPreferenceUpdating(true)
		setPreferenceError(null)

		try {
			await updatePreferences({ [key]: value })
		} catch (e: any) {
			setPreferenceError(e?.message || 'Failed to save preference.')
			await refresh()
		} finally {
			preferenceUpdateInFlightRef.current = false
			setPreferenceUpdating(false)
		}
	}

	const handleNotificationToggle = (v: boolean) => {
		hapticFeedback.selection()
		void updatePreference('notifications_enabled', v)
	}
	const handleDarkModeToggle = (v: boolean) => {
		hapticFeedback.selection()
		void updatePreference('dark_mode_enabled', v)
	}
	const handleAnalyticsToggle = (v: boolean) => {
		hapticFeedback.selection()
		void updatePreference('analytics_enabled', v)
	}

	const handleEditProfile = () => {
		if (!profile) {
			Alert.alert(
				'Profile unavailable',
				profileLoading ? 'Profile is still loading.' : 'Could not load profile data.',
			)
			return
		}
		setEditName((profile.name as string) || '')
		setEditPosition((profile.position as string) || '')
		const serverSkill = ((profile.skill_level as string) || 'beginner') as
			| 'beginner'
			| 'intermediate'
			| 'advanced'
		setEditSkillLevel(serverSkill)
		setShowEditModal(true)
	}

	const handleSaveProfile = async () => {
		if (!editName.trim()) { Alert.alert('Error', 'Name is required.'); return }
		setActionLoading(true)
		setActionError(null)
		try {
			await updateProfile({
				name: editName.trim(),
				position: editPosition,
				skillLevel: editSkillLevel,
			} as any)
			await refresh()
			setShowEditModal(false)
			hapticFeedback.success()
			Alert.alert('Profile Updated', 'Your profile has been saved.')
		} catch (e: any) {
			const message = e?.message || 'Failed to save profile.'
			setActionError(message)
			Alert.alert('Error', message)
		}
		finally { setActionLoading(false) }
	}

	const handleExportData = async () => {
		if (!user?.email) { Alert.alert('Error', 'Email is required to export data.'); return }
		setActionLoading(true)
		setActionError(null)
		try {
			const exportPayload = await apiService.exportUserData()
			const data = JSON.stringify(exportPayload, null, 2)
			await emailService.sendDataExportEmail(user.email, data)
			Alert.alert('Export Sent', 'Check your email for the data export.')
		} catch (e: any) {
			const message = e?.message || 'Failed to export data.'
			setActionError(message)
			Alert.alert('Error', message)
		}
		finally { setActionLoading(false) }
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
						setActionLoading(true)
						setActionError(null)
						try {
							await apiService.deleteAccount()
							try {
								await logout()
							} catch {
								await storageService.clearAllData()
							}
							Alert.alert('Account Deleted', 'Your account has been removed.')
						} catch (e: any) {
							setActionError(e?.message || 'Failed to delete account.')
							Alert.alert(
								'Error',
								e?.message || 'Failed to delete account.',
							)
						} finally {
							setActionLoading(false)
						}
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
					setActionLoading(true)
					setActionError(null)
					try { await logout() }
					catch (e: any) {
						const message = e?.message || 'Failed to sign out.'
						setActionError(message)
						Alert.alert('Error', message)
					}
					finally { setActionLoading(false) }
				},
			},
		])
	}

	const initials = useMemo(() => {
		const n = (profile?.name as string) || (profileLoading ? '...' : 'P')
		const parts = n.split(' ')
		return parts.length >= 2 ? `${parts[0][0]}${parts[1][0]}`.toUpperCase() : n[0].toUpperCase()
	}, [profile?.name, profileLoading])

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			{actionLoading ? (
				<View style={styles.loadingOverlay}>
					<ActivityIndicator size="large" color={colors.brand.orange} />
					<Text style={styles.loadingText}>Processing...</Text>
				</View>
			) : null}

			{networkToastMessage ? (
				<View style={styles.toastContainer} pointerEvents="none" testID="profile-network-toast">
					<Text style={styles.toastText}>{networkToastMessage}</Text>
				</View>
			) : null}

			<ScrollView showsVerticalScrollIndicator={false}>
				{blockingErrorMessage ? (
					<View style={styles.errorBanner}>
						<Text style={styles.errorText}>
							{blockingErrorMessage}
						</Text>
						<TouchableOpacity
							onPress={() => {
								setActionError(null)
								void refresh()
							}}
							activeOpacity={0.75}
						>
							<Text style={styles.retryText}>Retry</Text>
						</TouchableOpacity>
					</View>
				) : null}

				{/* Profile Hero */}
				<View style={styles.heroCard}>
					<View style={styles.avatarCircle}>
						<Text style={styles.avatarInitials}>{initials}</Text>
					</View>
					<Text style={styles.userName}>
						{(profile?.name as string) || (profileLoading ? 'Loading profile...' : 'Profile unavailable')}
					</Text>
					{profile?.username ? (
						<Text style={styles.userHandle}>@{String(profile.username)}</Text>
					) : null}
					{profileLoading ? <Text style={styles.syncText}>Syncing profile...</Text> : null}
					<TouchableOpacity onPress={handleEditProfile} style={styles.editBtn} activeOpacity={0.75}>
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
				{statsLoading ? <Text style={styles.syncText}>Syncing stats...</Text> : null}

				{/* Preferences */}
				<View style={styles.section}>
					<SectionHeader title="Preferences" />
					<View style={styles.prefRow}>
						<View style={styles.prefLeft}>
							<Ionicons name="notifications-outline" size={20} color={colors.text.secondary} />
							<Text style={styles.prefLabel}>Notifications</Text>
						</View>
						<Switch
							value={preferences.notifications_enabled}
							onValueChange={handleNotificationToggle}
							disabled={preferenceUpdating}
							trackColor={{ false: colors.bg.elevated, true: colors.brand.orangeDim }}
							thumbColor={preferences.notifications_enabled ? colors.brand.orange : colors.text.tertiary}
							accessibilityLabel="Notifications"
							accessibilityHint="When on, you can receive training reminders and app updates"
						/>
					</View>
					<View style={styles.prefRow}>
						<View style={styles.prefLeft}>
							<Ionicons name="moon-outline" size={20} color={colors.text.secondary} />
							<Text style={styles.prefLabel}>Dark Mode</Text>
						</View>
						<Switch
							value={preferences.dark_mode_enabled}
							onValueChange={handleDarkModeToggle}
							disabled={preferenceUpdating}
							trackColor={{ false: colors.bg.elevated, true: colors.brand.orangeDim }}
							thumbColor={preferences.dark_mode_enabled ? colors.brand.orange : colors.text.tertiary}
							accessibilityLabel="Dark mode"
							accessibilityHint="SHOOTRZ currently uses a dark interface only; this toggle is for future theming"
						/>
					</View>
					<View style={styles.prefRow}>
						<View style={styles.prefLeft}>
							<Ionicons name="analytics-outline" size={20} color={colors.text.secondary} />
							<Text style={styles.prefLabel}>Analytics</Text>
						</View>
						<Switch
							value={preferences.analytics_enabled}
							onValueChange={handleAnalyticsToggle}
							disabled={preferenceUpdating}
							trackColor={{ false: colors.bg.elevated, true: colors.brand.orangeDim }}
							thumbColor={preferences.analytics_enabled ? colors.brand.orange : colors.text.tertiary}
							accessibilityLabel="Product analytics"
							accessibilityHint="When on, uses anonymous data to help improve the app"
						/>
					</View>
					{preferenceUpdating ? (
						<Text style={styles.syncText}>Saving preferences...</Text>
					) : null}
				</View>

				{/* Account Actions */}
				<View style={styles.section}>
					<SectionHeader title="Account" />
					<TouchableOpacity style={styles.actionRow} onPress={handleExportData} activeOpacity={0.75}>
						<Ionicons name="download-outline" size={20} color={colors.text.secondary} />
						<Text style={styles.actionLabel}>Export Data</Text>
						<Ionicons name="chevron-forward" size={16} color={colors.text.tertiary} />
					</TouchableOpacity>
					<TouchableOpacity style={styles.actionRow} onPress={handleDeleteAccount} activeOpacity={0.75}>
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
										activeOpacity={0.8}
									>
										<Text style={[styles.skillPillText, editSkillLevel === level && styles.skillPillTextActive]}>
											{level.charAt(0).toUpperCase() + level.slice(1)}
										</Text>
									</TouchableOpacity>
								))}
							</View>
						</View>
						<PrimaryButton label="Save" onPress={handleSaveProfile} loading={actionLoading} fullWidth />
						<TouchableOpacity onPress={() => setShowEditModal(false)} style={styles.modalCancel} activeOpacity={0.75}>
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
		backgroundColor: glass.sheet.bg,
		alignItems: 'center',
		justifyContent: 'center',
		zIndex: 10,
	},
	loadingText: { ...typography.roles.body, color: colors.text.secondary, marginTop: spacing[3] },
	toastContainer: {
		position: 'absolute',
		top: spacing[4],
		left: spacing.screenPadding,
		right: spacing.screenPadding,
		zIndex: 12,
		borderRadius: radius.lg,
		paddingHorizontal: spacing[3],
		paddingVertical: spacing[3],
		backgroundColor: colors.bg.secondary,
		borderWidth: 1,
		borderColor: colors.brand.orange,
	},
	toastText: {
		...typography.roles.caption,
		color: colors.text.primary,
	},
	errorBanner: {
		marginHorizontal: spacing.screenPadding,
		marginTop: spacing[4],
		padding: spacing[3],
		borderRadius: radius.lg,
		borderWidth: 1,
		borderColor: colors.error,
		backgroundColor: colors.bg.secondary,
	},
	errorText: { ...typography.roles.caption, color: colors.error },
	retryText: {
		...typography.roles.caption,
		color: colors.brand.orange,
		marginTop: spacing[2],
		fontWeight: typography.weight.semibold,
		fontFamily: 'DMSansSemiBold',
	},
	syncText: {
		...typography.roles.caption,
		color: colors.text.tertiary,
		textAlign: 'center' as const,
		marginTop: spacing[2],
	},
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
		...typography.roles.headingMd,
		color: colors.text.inverse,
	},
	userName: {
		...typography.roles.headingLg,
		color: colors.text.primary,
		textAlign: 'center' as const,
	},
	userHandle: {
		...typography.roles.caption,
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
		...typography.roles.caption,
		color: colors.brand.orange,
		fontWeight: typography.weight.semibold,
		fontFamily: 'DMSansSemiBold',
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
	prefLabel: { ...typography.roles.body, color: colors.text.primary },
	actionRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[3],
		paddingVertical: spacing[3],
		borderBottomWidth: 1,
		borderBottomColor: colors.border.subtle,
	},
	actionLabel: { flex: 1, ...typography.roles.body, color: colors.text.primary },
	signOutSection: {
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing[8],
	},
	modalOverlay: {
		flex: 1,
		backgroundColor: glass.sheet.bg,
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
		...typography.roles.headingLg,
		color: colors.text.primary,
		textAlign: 'center',
		marginBottom: spacing[5],
	},
	modalField: { marginBottom: spacing[4] },
	modalLabel: { ...typography.roles.caption, color: colors.text.secondary, fontWeight: typography.weight.semibold, fontFamily: 'DMSansSemiBold', marginBottom: spacing[1] },
	modalInput: {
		backgroundColor: colors.bg.secondary,
		borderWidth: 1,
		borderColor: colors.border.default,
		borderRadius: radius.md,
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
		...typography.roles.body,
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
	skillPillText: { ...typography.roles.caption, color: colors.text.secondary },
	skillPillTextActive: { ...typography.roles.bodyStrong, color: colors.brand.orangeLight },
	modalCancel: { alignItems: 'center', paddingVertical: spacing[3], marginTop: spacing[2] },
	modalCancelText: { ...typography.roles.caption, color: colors.text.tertiary },
})
