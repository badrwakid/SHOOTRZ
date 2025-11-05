import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { Ionicons } from '@expo/vector-icons'
import { SHOOTRZ_THEME } from '../constants/theme'

interface MetricCardProps {
	title: string
	description?: string
	value: number
	unit: string
	optimalRange?: [number, number]
	score?: number // 0-25 score for this metric
	confidence?: number // 0-1 confidence
	color?: string
	icon?: keyof typeof Ionicons.glyphMap
	showScore?: boolean // Whether to show score indicator
}

export const MetricCard: React.FC<MetricCardProps> = ({
	title,
	description,
	value,
	unit,
	optimalRange,
	score,
	confidence,
	color = SHOOTRZ_THEME.colors.primary,
	icon,
	showScore = true,
}) => {
	// Determine performance color
	const getPerformanceColor = () => {
		if (!score) return SHOOTRZ_THEME.colors.textSecondary
		if (score >= 20) return SHOOTRZ_THEME.colors.success
		if (score >= 15) return SHOOTRZ_THEME.colors.primary
		if (score >= 10) return SHOOTRZ_THEME.colors.warning
		return SHOOTRZ_THEME.colors.error
	}

	const performanceColor = getPerformanceColor()
	const scorePercentage = score ? (score / 25) * 100 : 0
	const isInOptimalRange = optimalRange
		? value >= optimalRange[0] && value <= optimalRange[1]
		: null

	return (
		<LinearGradient
			colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
			start={{ x: 0, y: 0 }}
			end={{ x: 1, y: 1 }}
			style={styles.container}
		>
			{/* Border accent */}
			<View style={[styles.borderAccent, { backgroundColor: color }]} />

			{/* Header */}
			<View style={styles.header}>
				{icon && (
					<Ionicons
						name={icon}
						size={24}
						color={color}
						style={styles.icon}
					/>
				)}
				<View style={styles.headerText}>
					<Text style={styles.title}>{title}</Text>
					{description && (
						<Text style={styles.description} numberOfLines={2}>
							{description}
						</Text>
					)}
				</View>
			</View>

			{/* Value Display */}
			{unit !== 'N/A' ? (
				<View style={styles.valueContainer}>
					<Text style={[styles.value, { color }]}>
						{typeof value === 'number' ? value.toFixed(1) : 'N/A'}
					</Text>
					{unit && <Text style={styles.unit}>{unit}</Text>}
				</View>
			) : (
				<View style={styles.valueContainer}>
					<Text style={[styles.value, { color: SHOOTRZ_THEME.colors.textSecondary, fontSize: 18 }]}>
						Coming Soon
					</Text>
				</View>
			)}

			{/* Optimal Range Indicator */}
			{optimalRange && (
				<View style={styles.rangeContainer}>
					<Text style={styles.rangeLabel}>
						Optimal: {optimalRange[0]}-{optimalRange[1]} {unit}
					</Text>
					<View style={styles.rangeIndicator}>
						<View style={styles.rangeBar}>
							<View
								style={[
									styles.rangeMarker,
									{
										left: `${Math.min(100, Math.max(0, ((value - optimalRange[0]) / (optimalRange[1] - optimalRange[0])) * 100))}%`,
										backgroundColor: isInOptimalRange ? SHOOTRZ_THEME.colors.success : SHOOTRZ_THEME.colors.warning,
									},
								]}
							/>
						</View>
						<View
							style={[
								styles.optimalZone,
								{
									left: '0%',
									width: '100%',
									backgroundColor: SHOOTRZ_THEME.colors.success + '20',
								},
							]}
						/>
					</View>
				</View>
			)}

			{/* Score and Confidence */}
			{showScore && (score !== undefined || confidence !== undefined) && (
				<View style={styles.footer}>
					{score !== undefined && (
						<View style={styles.scoreContainer}>
							<View style={styles.scoreBar}>
								<View
									style={[
										styles.scoreFill,
										{
											width: `${scorePercentage}%`,
											backgroundColor: performanceColor,
										},
									]}
								/>
							</View>
							<Text style={[styles.scoreText, { color: performanceColor }]}>
								{Math.round(score)}/25
							</Text>
						</View>
					)}
					{confidence !== undefined && (
						<View style={styles.confidenceContainer}>
							<Ionicons
								name="checkmark-circle"
								size={16}
								color={confidence > 0.7 ? SHOOTRZ_THEME.colors.success : confidence > 0.5 ? SHOOTRZ_THEME.colors.warning : SHOOTRZ_THEME.colors.error}
							/>
							<Text style={styles.confidenceText}>
								{Math.round(confidence * 100)}%
							</Text>
						</View>
					)}
				</View>
			)}
		</LinearGradient>
	)
}

const styles = StyleSheet.create({
	container: {
		borderRadius: SHOOTRZ_THEME.borderRadius.lg,
		padding: SHOOTRZ_THEME.spacing.lg,
		marginVertical: SHOOTRZ_THEME.spacing.sm,
		position: 'relative',
		overflow: 'hidden',
	},
	borderAccent: {
		position: 'absolute',
		left: 0,
		top: 0,
		bottom: 0,
		width: 4,
		borderTopLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
		borderBottomLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
	},
	header: {
		flexDirection: 'row',
		alignItems: 'flex-start',
		marginBottom: SHOOTRZ_THEME.spacing.md,
	},
	icon: {
		marginRight: SHOOTRZ_THEME.spacing.sm,
		marginTop: 2,
	},
	headerText: {
		flex: 1,
	},
	title: {
		...SHOOTRZ_THEME.typography.heading3,
		marginBottom: 4,
	},
	description: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		fontSize: 12,
	},
	valueContainer: {
		flexDirection: 'row',
		alignItems: 'baseline',
		marginBottom: SHOOTRZ_THEME.spacing.md,
	},
	value: {
		...SHOOTRZ_THEME.typography.heading1,
		fontSize: 36,
		marginRight: SHOOTRZ_THEME.spacing.xs,
	},
	unit: {
		...SHOOTRZ_THEME.typography.body,
		color: SHOOTRZ_THEME.colors.textSecondary,
		fontSize: 16,
	},
	rangeContainer: {
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	rangeLabel: {
		...SHOOTRZ_THEME.typography.caption,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginBottom: 6,
	},
	rangeIndicator: {
		height: 6,
		position: 'relative',
		borderRadius: 3,
		overflow: 'hidden',
	},
	rangeBar: {
		height: '100%',
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		borderRadius: 3,
		position: 'relative',
	},
	optimalZone: {
		position: 'absolute',
		top: 0,
		height: '100%',
		borderRadius: 3,
	},
	rangeMarker: {
		position: 'absolute',
		top: 0,
		width: 4,
		height: '100%',
		borderRadius: 2,
		transform: [{ translateX: -2 }],
	},
	footer: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		marginTop: SHOOTRZ_THEME.spacing.xs,
	},
	scoreContainer: {
		flex: 1,
		flexDirection: 'row',
		alignItems: 'center',
		marginRight: SHOOTRZ_THEME.spacing.md,
	},
	scoreBar: {
		flex: 1,
		height: 6,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		borderRadius: 3,
		overflow: 'hidden',
		marginRight: SHOOTRZ_THEME.spacing.sm,
	},
	scoreFill: {
		height: '100%',
		borderRadius: 3,
	},
	scoreText: {
		...SHOOTRZ_THEME.typography.caption,
		fontWeight: '600',
		minWidth: 40,
	},
	confidenceContainer: {
		flexDirection: 'row',
		alignItems: 'center',
	},
	confidenceText: {
		...SHOOTRZ_THEME.typography.caption,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginLeft: 4,
	},
})
