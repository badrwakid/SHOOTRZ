import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, shadows } from '../constants/theme'

interface StreakBadgeProps {
	count: number
	active?: boolean
}

export function StreakBadge({ count, active = true }: StreakBadgeProps) {
	return (
		<View style={[styles.badge, active && shadows.orange]}>
			<Ionicons
				name="flame"
				size={16}
				color={active ? colors.brand.orange : colors.text.tertiary}
			/>
			<Text style={[styles.count, !active && styles.inactive]}>
				{count}
			</Text>
			<Text style={[styles.label, !active && styles.inactive]}>
				DAY STREAK
			</Text>
		</View>
	)
}

const styles = StyleSheet.create({
	badge: {
		flexDirection: 'row',
		alignItems: 'center',
		backgroundColor: colors.brand.orangeDim,
		borderRadius: radius.pill,
		paddingHorizontal: spacing[3],
		paddingVertical: spacing[1],
		gap: spacing[1],
	},
	count: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.bold,
		color: colors.brand.chrome,
	},
	label: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		color: colors.text.secondary,
		letterSpacing: typography.tracking.wider,
	},
	inactive: {
		color: colors.text.tertiary,
	},
})
