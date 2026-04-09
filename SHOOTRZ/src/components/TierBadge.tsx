import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { colors, typography, radius, spacing } from '../constants/theme'
import type { ScoreTier } from '../constants/theme'

interface TierBadgeProps {
	tier: ScoreTier
	size?: 'sm' | 'md'
}

const TIER_LABELS: Record<ScoreTier, string> = {
	elite: 'ELITE',
	great: 'GREAT',
	good: 'GOOD',
	fair: 'FAIR',
	poor: 'POOR',
}

export function TierBadge({ tier, size = 'sm' }: TierBadgeProps) {
	const tierColor = colors.score[tier]

	return (
		<View
			style={[
				styles.base,
				{
					backgroundColor: tierColor.bg,
					paddingVertical: size === 'sm' ? 2 : 4,
					paddingHorizontal: size === 'sm' ? spacing[2] : spacing[3],
				},
			]}
		>
			<Text style={[styles.label, { color: tierColor.text }]}>
				{TIER_LABELS[tier]}
			</Text>
		</View>
	)
}

const styles = StyleSheet.create({
	base: {
		borderRadius: radius.pill,
		alignSelf: 'flex-start',
	},
	label: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.wider,
	},
})
