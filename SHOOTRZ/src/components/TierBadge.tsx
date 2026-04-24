import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { typography, radius, spacing } from '../constants/theme'
import type { ScoreTier } from '../constants/theme'
import { SCORE_TIER_BADGE, SCORE_TIER_LABELS } from '../theme/scoreTier'

interface TierBadgeProps {
	tier: ScoreTier
	size?: 'sm' | 'md'
}

export function TierBadge({ tier, size = 'sm' }: TierBadgeProps) {
	const tierColor = SCORE_TIER_BADGE[tier]

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
				{SCORE_TIER_LABELS[tier]}
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
		...typography.roles.caption,
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.wider,
		textTransform: 'uppercase',
	},
})
