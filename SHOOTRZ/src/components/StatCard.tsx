import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius } from '../constants/theme'

interface StatCardProps {
	icon: string
	label: string
	value: string | number
	unit?: string
	subtitle?: string
	color?: 'orange' | 'cyan' | 'default'
}

export function StatCard({
	icon,
	label,
	value,
	unit,
	subtitle,
	color = 'default',
}: StatCardProps) {
	const tint =
		color === 'orange'
			? colors.brand.orange
			: color === 'cyan'
				? colors.brand.cyan
				: colors.brand.chrome
	const bgTint =
		color === 'orange'
			? colors.brand.orangeDim
			: color === 'cyan'
				? colors.brand.cyanDim
				: colors.brand.chromeDim

	return (
		<View style={styles.card}>
			<View style={[styles.iconWrap, { backgroundColor: bgTint }]}>
				<Ionicons name={icon as any} size={18} color={tint} />
			</View>
			<Text style={styles.value}>
				{value}
				{unit ? <Text style={styles.unit}> {unit}</Text> : null}
			</Text>
			<Text style={styles.label}>{label}</Text>
			{subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
		</View>
	)
}

const styles = StyleSheet.create({
	card: {
		flex: 1,
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		borderWidth: 1,
		borderColor: colors.border.default,
		padding: spacing[3],
		alignItems: 'center',
	},
	iconWrap: {
		width: 36,
		height: 36,
		borderRadius: 18,
		alignItems: 'center',
		justifyContent: 'center',
		marginBottom: spacing[2],
	},
	value: {
		fontSize: typography.size.xl,
		fontWeight: typography.weight.black,
		color: colors.text.primary,
	},
	unit: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.regular,
		color: colors.text.secondary,
	},
	label: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		color: colors.text.secondary,
		letterSpacing: typography.tracking.wide,
		marginTop: 2,
		textTransform: 'uppercase',
	},
	subtitle: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
		marginTop: 2,
	},
})
