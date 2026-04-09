import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius } from '../constants/theme'
import { ProgressBar } from './ProgressBar'

interface WorkoutCardProps {
	name: string
	drillCount: number
	estimatedMinutes: number
	difficulty: string
	progress: number
	onPress: () => void
}

export function WorkoutCard({
	name,
	drillCount,
	estimatedMinutes,
	difficulty,
	progress,
	onPress,
}: WorkoutCardProps) {
	const completedDrills = Math.round(drillCount * progress)
	const progressLabel =
		progress === 0
			? 'Not started'
			: `${completedDrills}/${drillCount} drills complete`

	return (
		<TouchableOpacity
			onPress={onPress}
			activeOpacity={0.85}
			accessibilityRole="button"
			style={styles.card}
		>
			<Text style={styles.name}>{name}</Text>
			<View style={styles.statsRow}>
				<View style={styles.stat}>
					<Ionicons name="basketball-outline" size={14} color={colors.text.secondary} />
					<Text style={styles.statText}>{drillCount} drills</Text>
				</View>
				<View style={styles.stat}>
					<Ionicons name="time-outline" size={14} color={colors.text.secondary} />
					<Text style={styles.statText}>{estimatedMinutes} min</Text>
				</View>
				<View style={[styles.difficultyPill, {
					backgroundColor:
						difficulty === 'beginner'
							? colors.success + '20'
							: difficulty === 'advanced'
								? colors.error + '20'
								: colors.warning + '20',
				}]}>
					<Text style={[styles.difficultyText, {
						color:
							difficulty === 'beginner'
								? colors.success
								: difficulty === 'advanced'
									? colors.error
									: colors.warning,
					}]}>
						{difficulty.toUpperCase()}
					</Text>
				</View>
			</View>
			<Text style={styles.progress}>{progressLabel}</Text>
			<ProgressBar progress={progress} height={4} />
		</TouchableOpacity>
	)
}

const styles = StyleSheet.create({
	card: {
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		borderWidth: 1,
		borderColor: colors.border.default,
		padding: spacing.cardPadding,
		gap: spacing[2],
	},
	name: {
		fontSize: typography.size.md,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
	},
	statsRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[3],
	},
	stat: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[1],
	},
	statText: {
		fontSize: typography.size.xs,
		color: colors.text.secondary,
	},
	difficultyPill: {
		paddingHorizontal: spacing[2],
		paddingVertical: 2,
		borderRadius: radius.pill,
	},
	difficultyText: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.wide,
	},
	progress: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
	},
})
