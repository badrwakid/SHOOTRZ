import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, glass, getScoreColor } from '../constants/theme'

interface MetricCardProps {
	label: string
	value: string | number
	unit?: string
	score?: number
	trend?: 'up' | 'down' | 'neutral'
	trendValue?: string
	description?: string
	onPress?: () => void
}

export function MetricCard({
	label,
	value,
	unit,
	score,
	trend,
	trendValue,
	description,
	onPress,
}: MetricCardProps) {
	const tierColor = score != null ? getScoreColor(score) : null
	const trendColor =
		trend === 'up' ? colors.success : trend === 'down' ? colors.error : colors.text.tertiary
	const trendIcon =
		trend === 'up' ? 'arrow-up' : trend === 'down' ? 'arrow-down' : 'remove'

	const content = (
		<View style={styles.card}>
			{tierColor ? (
				<View style={[styles.accent, { backgroundColor: tierColor.bg }]} />
			) : null}
			<View style={styles.body}>
				<Text style={styles.label}>{label.toUpperCase()}</Text>
				<View style={styles.valueRow}>
					<Text style={styles.value}>{value}</Text>
					{unit ? <Text style={styles.unit}>{unit}</Text> : null}
					{trend && trendValue ? (
						<View style={[styles.trendPill, { backgroundColor: trendColor + '20' }]}>
							<Ionicons name={trendIcon as any} size={10} color={trendColor} />
							<Text style={[styles.trendText, { color: trendColor }]}>{trendValue}</Text>
						</View>
					) : null}
				</View>
				{score != null && tierColor ? (
					<View style={styles.scoreBar}>
						<View
							style={[
								styles.scoreFill,
								{
									width: `${Math.min(score, 100)}%`,
									backgroundColor: tierColor.bg,
								},
							]}
						/>
					</View>
				) : null}
				{description ? <Text style={styles.description}>{description}</Text> : null}
			</View>
		</View>
	)

	if (onPress) {
		return (
			<TouchableOpacity onPress={onPress} activeOpacity={0.85}>
				{content}
			</TouchableOpacity>
		)
	}

	return content
}

const styles = StyleSheet.create({
	card: {
		flexDirection: 'row',
		backgroundColor: glass.card.bg,
		borderWidth: 1,
		borderColor: glass.card.border,
		borderRadius: radius.card,
		overflow: 'hidden',
	},
	accent: {
		width: 3,
	},
	body: {
		flex: 1,
		padding: spacing.cardPadding,
	},
	label: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		color: colors.text.secondary,
		letterSpacing: typography.tracking.widest,
		marginBottom: spacing[1],
	},
	valueRow: {
		flexDirection: 'row',
		alignItems: 'baseline',
		gap: spacing[1],
	},
	value: {
		fontSize: typography.size['2xl'],
		fontWeight: typography.weight.black,
		color: colors.text.primary,
	},
	unit: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.regular,
		color: colors.text.secondary,
	},
	trendPill: {
		flexDirection: 'row',
		alignItems: 'center',
		borderRadius: radius.pill,
		paddingHorizontal: spacing[2],
		paddingVertical: 2,
		marginLeft: spacing[2],
		gap: 2,
	},
	trendText: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.semibold,
	},
	scoreBar: {
		height: 3,
		backgroundColor: colors.bg.elevated,
		borderRadius: 2,
		marginTop: spacing[2],
		overflow: 'hidden',
	},
	scoreFill: {
		height: '100%',
		borderRadius: 2,
	},
	description: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
		marginTop: spacing[1],
	},
})
