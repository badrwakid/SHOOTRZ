import React, { useState, useEffect } from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	TouchableOpacity,
	RefreshControl,
	FlatList,
	Dimensions,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, glass, shadows, getScoreTier } from '../constants/theme'
import { ScoreRing } from '../components/ScoreRing'
import { StatCard } from '../components/StatCard'
import { StreakBadge } from '../components/StreakBadge'
import { TierBadge } from '../components/TierBadge'
import { SectionHeader } from '../components/SectionHeader'
import { AnalysisCard } from '../components/AnalysisCard'
import { PrimaryButton } from '../components/PrimaryButton'
import { SkeletonLoader } from '../components/SkeletonLoader'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../context/AuthContext'
import { apiService } from '../services/api.service'
import { storageService } from '../services/storage.service'
import { hapticFeedback } from '../utils/hapticFeedback'

const { width: SCREEN_WIDTH } = Dimensions.get('window')

interface HomeScreenProps {
	navigation: any
}

function getGreeting(): string {
	const h = new Date().getHours()
	if (h < 12) return 'Good morning'
	if (h < 17) return 'Good afternoon'
	return 'Good evening'
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
	const { user } = useAuth()
	const [loading, setLoading] = useState(true)
	const [refreshing, setRefreshing] = useState(false)
	const [stats, setStats] = useState({ dayStreak: 0, totalAnalyses: 0, averageScore: 0, bestScore: 0 })
	const [lastSession, setLastSession] = useState<{ score: number; date: string } | null>(null)
	const [recentSessions, setRecentSessions] = useState<any[]>([])

	useEffect(() => { loadData() }, [])
	useEffect(() => {
		const unsub = navigation.addListener('focus', () => loadData())
		return unsub
	}, [navigation])

	const loadData = async () => {
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
				setStats({
					dayStreak: serverStreak?.currentStreak ?? 0,
					totalAnalyses: serverStats.totalSessions ?? 0,
					averageScore: Math.round(serverStats.avgScore ?? 0),
					bestScore: Math.round(serverStats.bestScore ?? 0),
				})

				if (serverStats.lastSessionDate) {
					setLastSession({
						score: Math.round(serverStats.bestScore ?? serverStats.avgScore ?? 0),
						date: fmtDate(serverStats.lastSessionDate),
					})
				} else {
					setLastSession(null)
				}
			} else {
				const [analysisHistory, workoutHistory, drillCompletions] = await Promise.all([
					storageService.getAnalysisHistory(),
					storageService.getWorkoutHistory(),
					storageService.getDrillCompletions(),
				])

				const totalScore = analysisHistory.reduce((s, a) => s + a.scores.total, 0)
				const avg = analysisHistory.length > 0 ? Math.round(totalScore / analysisHistory.length) : 0
				const best = analysisHistory.length > 0 ? Math.max(...analysisHistory.map(a => a.scores.total)) : 0
				const streak = calcStreak(analysisHistory, workoutHistory, drillCompletions)

				setStats({ dayStreak: streak, totalAnalyses: analysisHistory.length, averageScore: avg, bestScore: best })

				if (analysisHistory.length > 0) {
					const latest = analysisHistory[0]
					setLastSession({ score: latest.scores.total, date: fmtDate(latest.timestamp) })
				} else {
					setLastSession(null)
				}

				setRecentSessions(
					analysisHistory.slice(0, 3).map(a => ({
						id: a.id,
						score: a.scores.total,
						date: fmtDate(a.timestamp),
					})),
				)
			}
		} catch (e) {
			console.error('Error loading dashboard:', e)
		} finally {
			setLoading(false)
		}
	}

	const calcStreak = (ah: any[], wh: any[], dc: any[]) => {
		const dates = new Set<string>()
		ah.forEach(a => dates.add(new Date(a.timestamp).toDateString()))
		wh.forEach(w => dates.add(new Date(w.completedAt).toDateString()))
		dc.forEach(d => dates.add(new Date(d.completedAt).toDateString()))
		if (dates.size === 0) return 0
		const sorted = Array.from(dates).sort((a, b) => new Date(b).getTime() - new Date(a).getTime())
		let streak = 0
		const today = new Date(); today.setHours(0, 0, 0, 0)
		for (let i = 0; i < sorted.length; i++) {
			const d = new Date(sorted[i]); d.setHours(0, 0, 0, 0)
			if (Math.floor((today.getTime() - d.getTime()) / 86400000) === i) streak++
			else break
		}
		return streak
	}

	const fmtDate = (iso: string) => {
		const d = new Date(iso)
		const now = new Date()
		const diff = Math.floor((now.getTime() - d.getTime()) / 86400000)
		if (diff === 0) return 'Today'
		if (diff === 1) return 'Yesterday'
		if (diff < 7) return `${diff} days ago`
		return d.toLocaleDateString()
	}

	const onRefresh = async () => {
		setRefreshing(true)
		await loadData()
		setRefreshing(false)
	}

	if (loading) {
		return (
			<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
				<View style={styles.skeletonHeader}>
					<SkeletonLoader width={200} height={24} />
					<SkeletonLoader width={120} height={16} />
				</View>
				<View style={styles.skeletonHero}>
					<SkeletonLoader width="100%" height={140} radius={16} />
				</View>
				<View style={styles.skeletonStats}>
					<SkeletonLoader width="30%" height={100} radius={16} />
					<SkeletonLoader width="30%" height={100} radius={16} />
					<SkeletonLoader width="30%" height={100} radius={16} />
				</View>
			</SafeAreaView>
		)
	}

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			<ScrollView
				showsVerticalScrollIndicator={false}
				refreshControl={
					<RefreshControl
						refreshing={refreshing}
						onRefresh={onRefresh}
						tintColor={colors.brand.orange}
					/>
				}
			>
				{/* Header */}
				<View style={styles.header}>
					<View>
						<Text style={styles.greeting}>
							{getGreeting()}, {user?.name?.split(' ')[0] || 'Player'}
						</Text>
						<Text style={styles.tagline}>PERFECT THE GAME</Text>
					</View>
					{stats.dayStreak > 0 ? <StreakBadge count={stats.dayStreak} /> : null}
				</View>

				{/* Hero Stat Card */}
				<View style={styles.heroCard}>
					{lastSession ? (
						<View style={styles.heroInner}>
							<ScoreRing score={lastSession.score} size="lg" animated />
							<View style={styles.heroInfo}>
								<Text style={styles.heroLabel}>LAST SESSION</Text>
								<Text style={styles.heroScore}>{lastSession.score}</Text>
								<TierBadge tier={getScoreTier(lastSession.score)} />
								<Text style={styles.heroDate}>{lastSession.date}</Text>
							</View>
						</View>
					) : (
						<EmptyState
							icon="basketball-outline"
							title="Your journey starts here"
							message="Analyze your first shot to see your score"
						/>
					)}
				</View>

				{/* Quick Stats */}
				<View style={styles.statsRow}>
					<StatCard icon="basketball" label="Sessions" value={stats.totalAnalyses} color="orange" />
					<StatCard icon="stats-chart" label="Avg Score" value={stats.averageScore} color="cyan" />
					<StatCard icon="trophy" label="Best" value={stats.bestScore} color="default" />
				</View>

				{/* Primary CTA */}
				<View style={styles.ctaWrap}>
					<PrimaryButton
						label="Analyze Shot"
						icon="camera"
						onPress={() => { hapticFeedback.medium(); navigation.navigate('Analyze') }}
						size="lg"
						fullWidth
					/>
				</View>

				{/* Coach J Card */}
				<TouchableOpacity
					style={styles.coachCard}
					onPress={() => navigation.navigate('Coach J')}
					activeOpacity={0.85}
				>
					<View style={styles.coachAvatar}>
						<Text style={styles.coachAvatarText}>J</Text>
					</View>
					<View style={styles.coachInfo}>
						<Text style={styles.coachName}>Coach J</Text>
						<Text style={styles.coachHint}>Ask me anything about your game...</Text>
					</View>
					<Ionicons name="chevron-forward" size={18} color={colors.brand.cyan} />
				</TouchableOpacity>

				{/* Recent Sessions */}
				{recentSessions.length > 0 ? (
					<View style={styles.section}>
						<SectionHeader
							title="Recent Sessions"
							action={{ label: 'See all', onPress: () => navigation.navigate('Progress') }}
						/>
						{recentSessions.map(s => (
							<View key={s.id} style={styles.sessionItem}>
								<AnalysisCard
									sessionId={s.id}
									date={s.date}
									score={s.score}
									onPress={() => navigation.navigate('Progress')}
								/>
							</View>
						))}
					</View>
				) : null}

				<View style={styles.bottomPad} />
			</ScrollView>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: colors.bg.primary,
	},
	header: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
		paddingHorizontal: spacing.screenPadding,
		paddingTop: spacing[4],
		paddingBottom: spacing[3],
	},
	greeting: {
		fontSize: typography.size.xl,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
	},
	tagline: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		color: colors.brand.cyan,
		letterSpacing: typography.tracking.widest,
		marginTop: 2,
	},
	heroCard: {
		marginHorizontal: spacing.screenPadding,
		marginTop: spacing[3],
		backgroundColor: glass.orange.bg,
		borderWidth: 1,
		borderColor: glass.orange.border,
		borderRadius: radius.card,
		padding: spacing.cardPadding,
		minHeight: 140,
	},
	heroInner: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[5],
	},
	heroInfo: {
		flex: 1,
	},
	heroLabel: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		color: colors.text.secondary,
		letterSpacing: typography.tracking.widest,
		marginBottom: spacing[1],
	},
	heroScore: {
		fontSize: typography.size['3xl'],
		fontWeight: typography.weight.black,
		color: colors.brand.chrome,
		marginBottom: spacing[2],
	},
	heroDate: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
		marginTop: spacing[2],
	},
	statsRow: {
		flexDirection: 'row',
		gap: spacing[3],
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing.sectionGap,
	},
	ctaWrap: {
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing.sectionGap,
	},
	coachCard: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[3],
		marginHorizontal: spacing.screenPadding,
		marginTop: spacing[4],
		backgroundColor: glass.cyan.bg,
		borderWidth: 1,
		borderColor: glass.cyan.border,
		borderRadius: radius.card,
		padding: spacing.cardPadding,
	},
	coachAvatar: {
		width: 40,
		height: 40,
		borderRadius: 20,
		backgroundColor: colors.brand.cyan,
		alignItems: 'center',
		justifyContent: 'center',
	},
	coachAvatarText: {
		fontSize: typography.size.md,
		fontWeight: typography.weight.bold,
		color: colors.bg.primary,
	},
	coachInfo: {
		flex: 1,
	},
	coachName: {
		fontSize: typography.size.base,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
	},
	coachHint: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
		marginTop: 2,
	},
	section: {
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing.sectionGap,
	},
	sessionItem: {
		marginBottom: spacing.itemGap,
	},
	bottomPad: {
		height: spacing.tabBarHeight,
	},
	skeletonHeader: {
		padding: spacing.screenPadding,
		gap: spacing[2],
	},
	skeletonHero: {
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing[3],
	},
	skeletonStats: {
		flexDirection: 'row',
		paddingHorizontal: spacing.screenPadding,
		gap: spacing[3],
		marginTop: spacing[4],
	},
})
