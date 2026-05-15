import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { spacing } from '../constants/theme'
import { useTokens } from '../theme/useTokens'

interface SectionHeaderProps {
	title: string
	subtitle?: string
	action?: { label: string; onPress: () => void }
}

export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
	const t = useTokens()

	return (
		<View style={styles.container}>
			<View style={styles.left}>
				<Text style={[t.typography.bodyStrong, { color: t.tokens.text.primary }]}>{title}</Text>
				{subtitle ? (
					<Text
						style={[
							t.typography.caption,
							{ color: t.tokens.text.secondary, marginTop: spacing[1] },
						]}
					>
						{subtitle}
					</Text>
				) : null}
			</View>
			{action ? (
				<TouchableOpacity
					onPress={action.onPress}
					hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
					accessibilityRole="button"
					accessibilityLabel={action.label}
				>
					<Text
						style={[
							t.typography.caption,
							{ color: t.tokens.brand.primary },
						]}
					>
						{action.label} →
					</Text>
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
})
