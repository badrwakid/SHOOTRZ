import React from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	TouchableOpacity,
	FlatList,
} from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { Ionicons } from '@expo/vector-icons'
import { SHOOTRZ_THEME } from '../constants/theme'

export interface Metric {
	metric_name: string
	value: number
	unit?: string
	confidence: number
	phase?: string
	timestamp_ms?: number
	frame_idx?: number
}

interface MetricsTableProps {
	metrics: Metric[]
	onMetricPress?: (metric: Metric) => void
	normativeRanges?: Record<string, { target_range?: [number, number] }>
}

export function MetricsTable({
	metrics,
	onMetricPress,
	normativeRanges = {},
}: MetricsTableProps) {
	const getMetricStatus = (metric: Metric): 'optimal' | 'warning' | 'error' => {
		const range = normativeRanges[metric.metric_name]?.target_range
		if (!range) return 'optimal'

		const [min, max] = range
		if (metric.value >= min && metric.value <= max) {
			return 'optimal'
		}
		// Determine if it's a warning (close) or error (far)
		const distanceFromRange = Math.min(
			Math.abs(metric.value - min),
			Math.abs(metric.value - max)
		)
		const rangeSize = max - min
		const threshold = rangeSize * 0.5 // 50% outside range = error

		return distanceFromRange > threshold ? 'error' : 'warning'
	}

	const getStatusColor = (status: 'optimal' | 'warning' | 'error') => {
		switch (status) {
			case 'optimal':
				return SHOOTRZ_THEME.colors.success
			case 'warning':
				return SHOOTRZ_THEME.colors.warning
			case 'error':
				return SHOOTRZ_THEME.colors.error
		}
	}

	const getMetricIcon = (metricName: string) => {
		const icons: Record<string, string> = {
			forearm_verticality: 'ellipse-outline',
			elbow_flexion_preparatory: 'body-outline',
			elbow_flexion_release: 'arrow-up-outline',
			knee_flexion: 'fitness-outline',
			hip_flexion: 'resize-outline',
			shoulder_angle: 'arrow-up-circle-outline',
			release_angle: 'radio-button-on-outline',
			entry_angle: 'arrow-down-circle-outline',
			arc_height: 'stats-chart-outline',
			release_height: 'trending-up-outline',
			wrist_angular_velocity: 'speedometer-outline',
			grip_quality: 'hand-left-outline',
		}
		return icons[metricName] || 'analytics-outline'
	}

	const formatMetricName = (name: string): string => {
		return name
			.replace(/_/g, ' ')
			.replace(/\b\w/g, (l) => l.toUpperCase())
	}

	const formatValue = (value: number, unit?: string): string => {
		const formatted = typeof value === 'number' ? value.toFixed(1) : String(value)
		return unit ? `${formatted} ${unit}` : formatted
	}

	const renderMetricRow = ({ item: metric }: { item: Metric }) => {
		const status = getMetricStatus(metric)
		const statusColor = getStatusColor(status)
		const range = normativeRanges[metric.metric_name]?.target_range

		return (
			<TouchableOpacity
				style={styles.row}
				onPress={() => onMetricPress?.(metric)}
				activeOpacity={onMetricPress ? 0.7 : 1}
			>
				<View style={styles.rowContent}>
					{/* Icon and Name */}
					<View style={styles.metricInfo}>
						<Ionicons
							name={getMetricIcon(metric.metric_name) as any}
							size={20}
							color={statusColor}
						/>
						<View style={styles.metricNameContainer}>
							<Text style={styles.metricName}>
								{formatMetricName(metric.metric_name)}
							</Text>
							{metric.phase && (
								<Text style={styles.metricPhase}>
									Phase: {metric.phase}
								</Text>
							)}
						</View>
					</View>

					{/* Value and Status */}
					<View style={styles.metricValueContainer}>
						<Text style={[styles.metricValue, { color: statusColor }]}>
							{formatValue(metric.value, metric.unit)}
						</Text>
						{range && (
							<Text style={styles.metricRange}>
								Target: {formatValue(range[0], metric.unit)} - {formatValue(range[1], metric.unit)}
							</Text>
						)}
					</View>
				</View>

				{/* Status Indicator */}
				<View style={[styles.statusIndicator, { backgroundColor: statusColor }]} />

				{/* Confidence Badge */}
				<View style={styles.confidenceBadge}>
					<Ionicons
						name="checkmark-circle"
						size={12}
						color={
							metric.confidence >= 0.7
								? SHOOTRZ_THEME.colors.success
								: metric.confidence >= 0.5
								? SHOOTRZ_THEME.colors.warning
								: SHOOTRZ_THEME.colors.error
						}
					/>
					<Text
						style={[
							styles.confidenceText,
							{
								color:
									metric.confidence >= 0.7
										? SHOOTRZ_THEME.colors.success
										: metric.confidence >= 0.5
										? SHOOTRZ_THEME.colors.warning
										: SHOOTRZ_THEME.colors.error,
							},
						]}
					>
						{Math.round(metric.confidence * 100)}%
					</Text>
				</View>

				{onMetricPress && (
					<Ionicons
						name="chevron-forward"
						size={16}
						color={SHOOTRZ_THEME.colors.textSecondary}
						style={styles.chevron}
					/>
				)}
			</TouchableOpacity>
		)
	}

	if (metrics.length === 0) {
		return (
			<View style={styles.emptyContainer}>
				<Ionicons name="analytics-outline" size={48} color={SHOOTRZ_THEME.colors.textSecondary} />
				<Text style={styles.emptyText}>No metrics available</Text>
			</View>
		)
	}

	return (
		<View style={styles.container}>
			<View style={styles.header}>
				<Text style={styles.headerTitle}>Analysis Metrics</Text>
				<Text style={styles.headerSubtitle}>
					{metrics.length} metric{metrics.length !== 1 ? 's' : ''} computed
				</Text>
			</View>

			<FlatList
				data={metrics}
				renderItem={renderMetricRow}
				keyExtractor={(item, index) => `${item.metric_name}-${index}`}
				scrollEnabled={false}
				contentContainerStyle={styles.listContent}
			/>
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: 12,
		padding: 16,
		marginVertical: 8,
	},
	header: {
		marginBottom: 16,
	},
	headerTitle: {
		fontSize: 20,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.text,
	},
	headerSubtitle: {
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 4,
	},
	listContent: {
		gap: 8,
	},
	row: {
		flexDirection: 'row',
		alignItems: 'center',
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		borderRadius: 8,
		padding: 12,
		marginVertical: 4,
	},
	rowContent: {
		flex: 1,
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
	},
	metricInfo: {
		flexDirection: 'row',
		alignItems: 'center',
		flex: 1,
	},
	metricNameContainer: {
		marginLeft: 12,
		flex: 1,
	},
	metricName: {
		fontSize: 15,
		fontWeight: '600',
		color: SHOOTRZ_THEME.colors.text,
	},
	metricPhase: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 2,
	},
	metricValueContainer: {
		alignItems: 'flex-end',
		marginLeft: 12,
	},
	metricValue: {
		fontSize: 16,
		fontWeight: '700',
	},
	metricRange: {
		fontSize: 11,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 2,
	},
	statusIndicator: {
		width: 4,
		height: 40,
		borderRadius: 2,
		marginHorizontal: 8,
	},
	confidenceBadge: {
		flexDirection: 'row',
		alignItems: 'center',
		paddingHorizontal: 6,
		paddingVertical: 2,
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: 8,
	},
	confidenceText: {
		fontSize: 10,
		fontWeight: '600',
		marginLeft: 4,
	},
	chevron: {
		marginLeft: 8,
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



