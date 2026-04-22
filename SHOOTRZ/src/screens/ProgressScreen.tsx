import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	TouchableOpacity,
	RefreshControl,
	Dimensions,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { LineChart } from 'react-native-chart-kit'
import { format, parseISO, subDays, isAfter } from 'date-fns'
import { apiService } from '../services/api.service'
import { useAuth } from '../context/AuthContext'
import { colors, typography, spacing, radius, glass } from '../constants/theme'
import { ScoreRing } from '../components/ScoreRing'
import { MetricCard } from '../components/MetricCard'
import { SectionHeader } from '../components/SectionHeader'
import { SkeletonLoader } from '../components/SkeletonLoader'
import { EmptyState } from '../components/EmptyState'
import { AnalysisCard } from '../components/AnalysisCard'
import { hapticFeedback } from '../utils/hapticFeedback'
import type { HistorySession } from '../types/contracts'

const SCREEN_W = Dimensions.get('window').width

interface Session {
	id: string
	date: string
	title?: string
	shot_count: number
	average_score?: number
	metrics?: Record<string, number>
}

interface MetricTrend {
	name: string
	data: { date: string; value: number }[]
}

type TimeRange = 'week' | 'month' | 'all'

export const ProgressScreen: React.FC = () => {
	const { user } = useAuth()
	const [loading, setLoading] = useState(true)
	const [refreshing, setRefreshing] = useState(false)
	const [sessions, setSessions] = useState<Session[]>([])
	const [metricTrends, setMetricTrends] = useState<MetricTrend[]>([])
	const [timeRange, setTimeRange] = useState<TimeRange>('month')

	const loadSessions = useCallback(async () => {
		if (!user?.id) { setLoading(false); return }
		try {
			const resp = await apiService.getAnalysisHistory(100, 0)
			const sessionList = resp?.sessions ?? []
			const mapped: Session[] = sessionList.map((h: HistorySession) => {
				const overall =
					h.overall_score != null
						? h.overall_score
						: h.average_score != null
							? h.average_score
							: undefined
				return {
					id: h.session_id ?? String(Date.now()),
					date: h.timestamp || h.date || new Date().toISOString(),
					title: h.title ?? undefined,
					shot_count: h.shot_count ?? 1,
					average_score: overall,
					metrics: h.metrics?.reduce((acc: Record<string, number>, m: any) => {
						const key = m.metric_name || m.name
						if (key && Number.isFinite(m.value)) acc[key] = m.value
						return acc
					}, {}),
				}
			})
			setSessions(mapped)
			calcTrends(mapped)
		} catch (e) {
			console.error('Error loading progress:', e)
		} finally {
			setLoading(false)
			setRefreshing(false)
		}
	}, [user])

	useEffect(() => { loadSessions() }, [loadSessions])

	const calcTrends = (data: Session[]) => {
		const metricsMap: Record<string, { date: string; value: number }[]> = {}
		data.forEach(s => {
			if (!s.metrics) return
			Object.entries(s.metrics).forEach(([k, v]) => {
				if (!metricsMap[k]) metricsMap[k] = []
				metricsMap[k].push({ date: s.date, value: v })
			})
		})
		setMetricTrends(
			Object.entries(metricsMap).map(([name, d]) => ({
				name,
				data: d.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()),
			})),
		)
	}

	const filteredSessions = useMemo(() => {
		if (timeRange === 'all') return sessions
		const cutoff = subDays(new Date(), timeRange === 'week' ? 7 : 30)
		return sessions.filter(s => isAfter(parseISO(s.date), cutoff))
	}, [sessions, timeRange])

	const avgScore = useMemo(() => {
		const scored = filteredSessions.filter(s => s.average_score != null)
		if (scored.length === 0) return 0
		return Math.round(scored.reduce((sum, s) => sum + (s.average_score || 0), 0) / scored.length)
	}, [filteredSessions])

	const chartData = useMemo(() => {
		const scored = filteredSessions.filter(s => s.average_score != null).slice(-10)
		return {
			labels: scored.map(s => { try { return format(parseISO(s.date), 'M/d') } catch { return '' } }),
			datasets: [{ data: scored.length > 0 ? scored.map(s => s.average_score || 0) : [0] }],
		}
	}, [filteredSessions])

	if (loading) {
		return (
			<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
				<View style={styles.skeleton}>
					<SkeletonLoader width="60%" height={24} />
					<SkeletonLoader width="100%" height={180} radius={16} style={{ marginTop: spacing[4] }} />
					<SkeletonLoader width="100%" height={100} radius={16} style={{ marginTop: spacing[4] }} />
				</View>
			</SafeAreaView>
		)
	}

	if (sessions.length === 0) {
		return (
			<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
				<EmptyState
					icon="stats-chart-outline"
					title="No sessions yet"
					message="Analyze your first shot to start tracking progress."
					action={{ label: 'Analyze a Shot', onPress: () => {} }}
				/>
			</SafeAreaView>
		)
	}

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			<ScrollView
				showsVerticalScrollIndicator={false}
				refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadSessions() }} tintColor={colors.brand.orange} />}
			>
				{/* Period Selector */}
				<View style={styles.periodRow}>
					{(['week', 'month', 'all'] as const).map(r => (
						<TouchableOpacity
							key={r}
							style={[styles.periodPill, timeRange === r && styles.periodPillActive]}
							onPress={() => { hapticFeedback.selection(); setTimeRange(r) }}
						>
							<Text style={[styles.periodText, timeRange === r && styles.periodTextActive]}>
								{r === 'all' ? 'All Time' : r.charAt(0).toUpperCase() + r.slice(1)}
							</Text>
						</TouchableOpacity>
					))}
				</View>

				{/* Overall Score */}
				<View style={styles.overallCard}>
					<ScoreRing score={avgScore} size="lg" animated />
					<View style={styles.overallInfo}>
						<Text style={styles.overallLabel}>AVERAGE SCORE</Text>
						<Text style={styles.overallValue}>{avgScore}</Text>
						<Text style={styles.overallSub}>{filteredSessions.length} session{filteredSessions.length !== 1 ? 's' : ''}</Text>
					</View>
				</View>

				{/* Chart */}
				{chartData.datasets[0].data.length > 1 ? (
					<View style={styles.section}>
						<SectionHeader title="Score Trend" />
						<LineChart
							data={chartData}
							width={SCREEN_W - spacing.screenPadding * 2}
							height={180}
							chartConfig={{
								backgroundColor: colors.bg.secondary,
								backgroundGradientFrom: colors.bg.secondary,
								backgroundGradientTo: colors.bg.elevated,
								decimalPlaces: 0,
								color: () => colors.brand.orange,
								labelColor: () => colors.text.tertiary,
								propsForDots: { r: '4', strokeWidth: '2', stroke: colors.brand.orangeLight },
							}}
							bezier
							style={styles.chart}
						/>
					</View>
				) : null}

				{/* Metric Trends */}
				{metricTrends.length > 0 ? (
					<View style={styles.section}>
						<SectionHeader title="Metric Improvements" />
						<View style={styles.metricsGrid}>
							{metricTrends.slice(0, 4).map(mt => {
								const latest = mt.data[mt.data.length - 1]?.value ?? 0
								const first = mt.data[0]?.value ?? 0
								const delta = latest - first
								return (
									<View key={mt.name} style={styles.metricItem}>
										<MetricCard
											label={mt.name.replace(/_/g, ' ')}
											value={latest.toFixed(1)}
											trend={delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral'}
											trendValue={`${delta >= 0 ? '+' : ''}${delta.toFixed(1)}`}
										/>
									</View>
								)
							})}
						</View>
					</View>
				) : null}

				{/* Session History */}
				<View style={styles.section}>
					<SectionHeader title="Session History" />
					{filteredSessions.map(s => (
						<View key={s.id} style={styles.sessionItem}>
							<AnalysisCard
								sessionId={s.id}
								date={(() => { try { return format(parseISO(s.date), 'MMM d, yyyy') } catch { return s.date } })()}
								score={s.average_score || 0}
								shotCount={s.shot_count}
								onPress={() => {}}
							/>
						</View>
					))}
				</View>

				<View style={{ height: spacing.tabBarHeight }} />
			</ScrollView>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: { flex: 1, backgroundColor: colors.bg.primary },
	skeleton: { padding: spacing.screenPadding, gap: spacing[2] },
	periodRow: {
		flexDirection: 'row',
		gap: spacing[2],
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[4],
	},
	periodPill: {
		flex: 1,
		paddingVertical: spacing[2],
		borderRadius: radius.pill,
		borderWidth: 1,
		borderColor: colors.border.default,
		alignItems: 'center',
	},
	periodPillActive: {
		backgroundColor: colors.brand.orange,
		borderColor: colors.brand.orange,
	},
	periodText: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
		fontWeight: typography.weight.medium,
	},
	periodTextActive: {
		color: colors.text.primary,
		fontWeight: typography.weight.bold,
	},
	overallCard: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[5],
		marginHorizontal: spacing.screenPadding,
		backgroundColor: glass.orange.bg,
		borderWidth: 1,
		borderColor: glass.orange.border,
		borderRadius: radius.card,
		padding: spacing.cardPadding,
	},
	overallInfo: { flex: 1 },
	overallLabel: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		color: colors.text.secondary,
		letterSpacing: typography.tracking.widest,
	},
	overallValue: {
		fontSize: typography.size['3xl'],
		fontWeight: typography.weight.black,
		color: colors.brand.chrome,
	},
	overallSub: {
		fontSize: typography.size.sm,
		color: colors.text.tertiary,
		marginTop: spacing[1],
	},
	section: {
		paddingHorizontal: spacing.screenPadding,
		marginTop: spacing.sectionGap,
	},
	chart: {
		borderRadius: radius.lg,
		marginTop: spacing[2],
	},
	metricsGrid: {
		flexDirection: 'row',
		flexWrap: 'wrap',
		gap: spacing[3],
	},
	metricItem: { width: '47%' },
	sessionItem: { marginBottom: spacing.itemGap },
})
