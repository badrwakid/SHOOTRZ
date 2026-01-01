import React, { useState, useEffect, useCallback } from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	Dimensions,
	ActivityIndicator,
	TouchableOpacity,
	RefreshControl,
} from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { format, parseISO, subDays, isAfter } from 'date-fns'
import { LineChart, BarChart } from 'react-native-chart-kit'
import { SHOOTRZ_THEME } from '../constants/theme'
import { apiService } from '../services/api.service'
import { useAuth } from '../context/AuthContext'
import { MetricsTable, Metric } from '../components/MetricsTable'

const { width: SCREEN_WIDTH } = Dimensions.get('window')
const CHART_WIDTH = SCREEN_WIDTH - 32

interface Session {
	id: string
	date: string
	title?: string
	shot_count: number
	average_score?: number
	metrics?: Metric[]
}

interface MetricTrend {
	metric_name: string
	values: Array<{ date: string; value: number }>
	unit?: string
	target_range?: [number, number]
}

export const ProgressScreen: React.FC = () => {
	const { user } = useAuth()
	const [loading, setLoading] = useState(true)
	const [refreshing, setRefreshing] = useState(false)
	const [sessions, setSessions] = useState<Session[]>([])
	const [selectedSession, setSelectedSession] = useState<Session | null>(null)
	const [metricTrends, setMetricTrends] = useState<MetricTrend[]>([])
	const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('month')
	const [selectedMetric, setSelectedMetric] = useState<string | null>(null)

	const loadSessions = useCallback(async () => {
		if (!user?.id) return

		try {
			// Fetch sessions from Supabase via API
			// This would call backend/routers/history.py endpoint
			
			// Mock structure - replace with actual API call
			const mockSessions: Session[] = []
			setSessions(mockSessions)
			
			// Calculate metric trends
			calculateMetricTrends(mockSessions)
		} catch (error) {
			console.error('Error loading sessions:', error)
		} finally {
			setLoading(false)
			setRefreshing(false)
		}
	}, [user])

	const calculateMetricTrends = (sessionsData: Session[]) => {
		if (sessionsData.length === 0) return

		// Group metrics by name across sessions
		const metricsMap: Record<string, MetricTrend> = {}

		sessionsData.forEach((session) => {
			if (!session.metrics) return

			session.metrics.forEach((metric) => {
				if (!metricsMap[metric.metric_name]) {
					metricsMap[metric.metric_name] = {
						metric_name: metric.metric_name,
						values: [],
						unit: metric.unit,
					}
				}

				metricsMap[metric.metric_name].values.push({
					date: session.date,
					value: metric.value,
				})
			})
		})

		// Sort values by date
		Object.values(metricsMap).forEach((trend) => {
			trend.values.sort((a, b) => 
				new Date(a.date).getTime() - new Date(b.date).getTime()
			)
		})

		setMetricTrends(Object.values(metricsMap))
	}

	useEffect(() => {
		loadSessions()
	}, [loadSessions])

	const onRefresh = useCallback(() => {
		setRefreshing(true)
		loadSessions()
	}, [loadSessions])

	const filterSessionsByTimeRange = (sessionsData: Session[]) => {
		const now = new Date()
		const cutoffDate = 
			timeRange === 'week' ? subDays(now, 7) :
			timeRange === 'month' ? subDays(now, 30) :
			new Date(0)

		return sessionsData.filter((session) => 
			isAfter(parseISO(session.date), cutoffDate)
		)
	}

	const getConsistencyScore = (metricName: string): number => {
		const trend = metricTrends.find((t) => t.metric_name === metricName)
		if (!trend || trend.values.length < 2) return 0

		const values = trend.values.map((v) => v.value)
		const mean = values.reduce((a, b) => a + b, 0) / values.length
		const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
		const stdDev = Math.sqrt(variance)
		
		// Consistency = inverse of coefficient of variation (higher = more consistent)
		if (mean === 0) return 0
		const cv = stdDev / Math.abs(mean)
		return Math.max(0, Math.min(100, 100 * (1 - cv)))
	}

	const renderTimeRangeSelector = () => (
		<View style={styles.timeRangeContainer}>
			{(['week', 'month', 'all'] as const).map((range) => (
				<TouchableOpacity
					key={range}
					style={[
						styles.timeRangeButton,
						timeRange === range && styles.timeRangeButtonActive,
					]}
					onPress={() => setTimeRange(range)}
				>
					<Text
						style={[
							styles.timeRangeText,
							timeRange === range && styles.timeRangeTextActive,
						]}
					>
						{range.charAt(0).toUpperCase() + range.slice(1)}
					</Text>
				</TouchableOpacity>
			))}
		</View>
	)

	const renderMetricTrendChart = (metricName: string) => {
		const trend = metricTrends.find((t) => t.metric_name === metricName)
		if (!trend || trend.values.length === 0) return null

		const data = {
			labels: trend.values.map((v, idx) => 
				idx % Math.ceil(trend.values.length / 5) === 0 
					? format(parseISO(v.date), 'MM/dd') 
					: ''
			).filter(Boolean),
			datasets: [
				{
					data: trend.values.map((v) => v.value),
					color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
					strokeWidth: 2,
				},
			],
		}

		const consistency = getConsistencyScore(metricName)

		return (
			<View style={styles.chartContainer}>
				<View style={styles.chartHeader}>
					<Text style={styles.chartTitle}>
						{metricName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
					</Text>
					<View style={styles.consistencyBadge}>
						<Ionicons name="trending-up" size={16} color={SHOOTRZ_THEME.colors.success} />
						<Text style={styles.consistencyText}>
							{Math.round(consistency)}% consistent
						</Text>
					</View>
				</View>
				<LineChart
					data={data}
					width={CHART_WIDTH}
					height={220}
					yAxisLabel=""
					yAxisSuffix={trend.unit ? ` ${trend.unit}` : ''}
					chartConfig={{
						backgroundColor: SHOOTRZ_THEME.colors.surface,
						backgroundGradientFrom: SHOOTRZ_THEME.colors.surface,
						backgroundGradientTo: SHOOTRZ_THEME.colors.surfaceElevated,
						decimalPlaces: 1,
						color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
						labelColor: (opacity = 1) => `rgba(107, 114, 128, ${opacity})`,
						style: {
							borderRadius: 16,
						},
						propsForDots: {
							r: '4',
							strokeWidth: '2',
							stroke: SHOOTRZ_THEME.colors.primary,
						},
					}}
					bezier
					style={styles.chart}
				/>
				{trend.target_range && (
					<View style={styles.targetRangeIndicator}>
						<Text style={styles.targetRangeText}>
							Target: {trend.target_range[0]} - {trend.target_range[1]} {trend.unit}
						</Text>
					</View>
				)}
			</View>
		)
	}

	const renderSessionsList = () => {
		const filteredSessions = filterSessionsByTimeRange(sessions)

		if (filteredSessions.length === 0) {
			return (
				<View style={styles.emptyContainer}>
					<Ionicons name="calendar-outline" size={48} color={SHOOTRZ_THEME.colors.textSecondary} />
					<Text style={styles.emptyText}>No sessions in this time range</Text>
				</View>
			)
		}

		return (
			<View style={styles.sessionsList}>
				{filteredSessions.map((session) => (
					<TouchableOpacity
						key={session.id}
						style={[
							styles.sessionCard,
							selectedSession?.id === session.id && styles.sessionCardSelected,
						]}
						onPress={() => setSelectedSession(session)}
					>
						<LinearGradient
							colors={[
								SHOOTRZ_THEME.colors.surface,
								SHOOTRZ_THEME.colors.surfaceElevated,
							]}
							style={styles.sessionCardGradient}
						>
							<View style={styles.sessionCardHeader}>
								<View>
									<Text style={styles.sessionDate}>
										{format(parseISO(session.date), 'MMM dd, yyyy')}
									</Text>
									{session.title && (
										<Text style={styles.sessionTitle}>{session.title}</Text>
									)}
								</View>
								<Ionicons
									name="chevron-forward"
									size={20}
									color={SHOOTRZ_THEME.colors.textSecondary}
								/>
							</View>
							<View style={styles.sessionStats}>
								<View style={styles.sessionStat}>
									<Ionicons name="videocam" size={16} color={SHOOTRZ_THEME.colors.primary} />
									<Text style={styles.sessionStatText}>
										{session.shot_count} shot{session.shot_count !== 1 ? 's' : ''}
									</Text>
								</View>
								{session.average_score && (
									<View style={styles.sessionStat}>
										<Ionicons name="star" size={16} color={SHOOTRZ_THEME.colors.accent} />
										<Text style={styles.sessionStatText}>
											Avg: {session.average_score.toFixed(1)}
										</Text>
									</View>
								)}
							</View>
						</LinearGradient>
					</TouchableOpacity>
				))}
			</View>
		)
	}

	const renderSessionComparison = () => {
		if (sessions.length < 2) return null

		const recentSessions = sessions.slice(-5).reverse()
		const sessionLabels = recentSessions.map((s) => format(parseISO(s.date), 'MM/dd'))
		const scoreData = recentSessions.map((s) => s.average_score || 0)

		return (
			<View style={styles.chartContainer}>
				<Text style={styles.chartTitle}>Recent Sessions Comparison</Text>
				<BarChart
					data={{
						labels: sessionLabels,
						datasets: [
							{
								data: scoreData,
							},
						],
					}}
					width={CHART_WIDTH}
					height={220}
					yAxisLabel=""
					yAxisSuffix=" pts"
					chartConfig={{
						backgroundColor: SHOOTRZ_THEME.colors.surface,
						backgroundGradientFrom: SHOOTRZ_THEME.colors.surface,
						backgroundGradientTo: SHOOTRZ_THEME.colors.surfaceElevated,
						decimalPlaces: 1,
						color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
						labelColor: (opacity = 1) => `rgba(107, 114, 128, ${opacity})`,
					}}
					style={styles.chart}
				/>
			</View>
		)
	}

	if (loading) {
		return (
			<SafeAreaView style={styles.container}>
				<View style={styles.loadingContainer}>
					<ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
					<Text style={styles.loadingText}>Loading progress...</Text>
				</View>
			</SafeAreaView>
		)
	}

	return (
		<SafeAreaView style={styles.container}>
			<ScrollView
				style={styles.scrollView}
				contentContainerStyle={styles.scrollContent}
				refreshControl={
					<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
				}
			>
				{/* Header */}
				<View style={styles.header}>
					<Text style={styles.headerTitle}>Progress & History</Text>
					<Text style={styles.headerSubtitle}>
						Track your improvement over time
					</Text>
				</View>

				{/* Time Range Selector */}
				{renderTimeRangeSelector()}

				{/* Metric Trends */}
				{selectedMetric && renderMetricTrendChart(selectedMetric)}

				{/* Metric Selector */}
				{metricTrends.length > 0 && (
					<View style={styles.metricSelector}>
						<Text style={styles.sectionTitle}>View Metric Trends</Text>
						<ScrollView horizontal showsHorizontalScrollIndicator={false}>
							{metricTrends.slice(0, 5).map((trend) => (
								<TouchableOpacity
									key={trend.metric_name}
									style={[
										styles.metricChip,
										selectedMetric === trend.metric_name && styles.metricChipActive,
									]}
									onPress={() => 
										setSelectedMetric(
											selectedMetric === trend.metric_name ? null : trend.metric_name
										)
									}
								>
									<Text
										style={[
											styles.metricChipText,
											selectedMetric === trend.metric_name && styles.metricChipTextActive,
										]}
									>
										{trend.metric_name.replace(/_/g, ' ')}
									</Text>
								</TouchableOpacity>
							))}
						</ScrollView>
					</View>
				)}

				{/* Session Comparison Chart */}
				{renderSessionComparison()}

				{/* Sessions List */}
				<View style={styles.section}>
					<Text style={styles.sectionTitle}>Sessions</Text>
					{renderSessionsList()}
				</View>

				{/* Selected Session Metrics */}
				{selectedSession && selectedSession.metrics && (
					<View style={styles.section}>
						<Text style={styles.sectionTitle}>Session Metrics</Text>
						<MetricsTable metrics={selectedSession.metrics} />
					</View>
				)}
			</ScrollView>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: SHOOTRZ_THEME.colors.background,
	},
	scrollView: {
		flex: 1,
	},
	scrollContent: {
		padding: 16,
	},
	loadingContainer: {
		flex: 1,
		alignItems: 'center',
		justifyContent: 'center',
	},
	loadingText: {
		marginTop: 12,
		fontSize: 16,
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	header: {
		marginBottom: 24,
	},
	headerTitle: {
		fontSize: 28,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.textPrimary,
	},
	headerSubtitle: {
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 4,
	},
	timeRangeContainer: {
		flexDirection: 'row',
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: 12,
		padding: 4,
		marginBottom: 20,
	},
	timeRangeButton: {
		flex: 1,
		paddingVertical: 8,
		paddingHorizontal: 12,
		borderRadius: 8,
		alignItems: 'center',
	},
	timeRangeButtonActive: {
		backgroundColor: SHOOTRZ_THEME.colors.primary,
	},
	timeRangeText: {
		fontSize: 14,
		fontWeight: '500',
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	timeRangeTextActive: {
		color: '#fff',
		fontWeight: '600',
	},
	section: {
		marginBottom: 24,
	},
	sectionTitle: {
		fontSize: 20,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.textPrimary,
		marginBottom: 12,
	},
	chartContainer: {
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: 12,
		padding: 16,
		marginBottom: 16,
	},
	chartHeader: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		marginBottom: 12,
	},
	chartTitle: {
		fontSize: 18,
		fontWeight: '600',
		color: SHOOTRZ_THEME.colors.textPrimary,
	},
	consistencyBadge: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: 4,
	},
	consistencyText: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.success,
		fontWeight: '500',
	},
	chart: {
		borderRadius: 16,
	},
	targetRangeIndicator: {
		marginTop: 8,
		paddingTop: 8,
		borderTopWidth: 1,
		borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
	},
	targetRangeText: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.textSecondary,
		textAlign: 'center',
	},
	metricSelector: {
		marginBottom: 20,
	},
	metricChip: {
		paddingHorizontal: 16,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		marginRight: 8,
	},
	metricChipActive: {
		backgroundColor: SHOOTRZ_THEME.colors.primary,
	},
	metricChipText: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.textSecondary,
		fontWeight: '500',
	},
	metricChipTextActive: {
		color: '#fff',
	},
	sessionsList: {
		gap: 12,
	},
	sessionCard: {
		borderRadius: 12,
		overflow: 'hidden',
	},
	sessionCardSelected: {
		borderWidth: 2,
		borderColor: SHOOTRZ_THEME.colors.primary,
	},
	sessionCardGradient: {
		padding: 16,
	},
	sessionCardHeader: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		marginBottom: 8,
	},
	sessionDate: {
		fontSize: 16,
		fontWeight: '600',
		color: SHOOTRZ_THEME.colors.textPrimary,
	},
	sessionTitle: {
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 2,
	},
	sessionStats: {
		flexDirection: 'row',
		gap: 16,
	},
	sessionStat: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: 4,
	},
	sessionStatText: {
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	emptyContainer: {
		alignItems: 'center',
		justifyContent: 'center',
		padding: 40,
	},
	emptyText: {
		fontSize: 16,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 12,
	},
})
