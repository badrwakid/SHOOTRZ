import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { colors, typography, spacing } from '../constants/theme'

interface SectionHeaderProps {
	title: string
	subtitle?: string
	action?: { label: string; onPress: () => void }
}

export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
	return (
		<View style={styles.container}>
			<View style={styles.left}>
				<Text style={styles.title}>{title}</Text>
				{subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
			</View>
			{action ? (
				<TouchableOpacity
					onPress={action.onPress}
					hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
					accessibilityRole="button"
					accessibilityLabel={action.label}
				>
					<Text style={styles.action}>{action.label} →</Text>
				</TouchableOpacity>
			) : null}
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		flexDirection: 'row',
		alignItems: 'flex-end',
		justifyContent: 'space-between',
		marginBottom: spacing[3],
	},
	left: {
		flex: 1,
	},
	title: {
		fontSize: typography.size.md,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
		letterSpacing: typography.tracking.tight,
	},
	subtitle: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
		marginTop: 2,
	},
	action: {
		fontSize: typography.size.sm,
		color: colors.brand.orange,
		fontWeight: typography.weight.semibold,
	},
})
