import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, getScoreTier } from '../constants/theme'
import { ScoreRing } from './ScoreRing'
import { TierBadge } from './TierBadge'

interface AnalysisCardProps {
	sessionId: string
	date: string
	score: number
	thumbnail?: string
	duration?: string
	shotCount?: number
	onPress?: () => void
}

export function AnalysisCard({
	date,
	score,
	duration,
	shotCount,
	onPress,
}: AnalysisCardProps) {
	const tier = getScoreTier(score)
	const a11yLabel = `Session on ${date}, score ${score}`

	const body = (
		<>
			<ScoreRing score={score} size="sm" animated={false} showTier={false} />
			<View style={styles.info}>
				<Text style={styles.date}>
					{date}
					{duration ? ` \u2022 ${duration}` : ''}
				</Text>
				{shotCount != null ? (
					<Text style={styles.shots}>{shotCount} shots analyzed</Text>
				) : null}
			</View>
			<View style={styles.right}>
				<TierBadge tier={tier} />
				{onPress ? <Ionicons name="chevron-forward" size={16} color={colors.text.tertiary} /> : null}
			</View>
		</>
	)

	if (onPress) {
		return (
			<TouchableOpacity
				onPress={onPress}
				activeOpacity={0.85}
				accessibilityRole="button"
				accessibilityLabel={a11yLabel}
				style={styles.card}
			>
				{body}
			</TouchableOpacity>
		)
	}

	return (
		<View
			style={styles.card}
			accessibilityLabel={a11yLabel}
			accessible
		>
			{body}
		</View>
	)
}

const styles = StyleSheet.create({
	card: {
		flexDirection: 'row',
		alignItems: 'center',
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		borderWidth: 1,
		borderColor: colors.border.default,
		padding: spacing[3],
		gap: spacing[3],
	},
	info: {
		flex: 1,
	},
	date: {
		...typography.roles.bodyStrong,
		color: colors.text.primary,
	},
	shots: {
		...typography.roles.caption,
		color: colors.text.secondary,
		marginTop: 2,
	},
	right: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[2],
	},
})
