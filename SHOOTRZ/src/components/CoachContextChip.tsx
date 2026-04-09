import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius } from '../constants/theme'

interface CoachContextChipProps {
	sessionLabel: string
	onDismiss?: () => void
}

export function CoachContextChip({ sessionLabel, onDismiss }: CoachContextChipProps) {
	return (
		<View style={styles.chip}>
			<Ionicons name="basketball" size={14} color={colors.brand.cyan} />
			<Text style={styles.label} numberOfLines={1}>
				Coaching: {sessionLabel}
			</Text>
			{onDismiss ? (
				<TouchableOpacity
					onPress={onDismiss}
					hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
					accessibilityLabel="Dismiss coaching context"
				>
					<Ionicons name="close-circle" size={16} color={colors.text.tertiary} />
				</TouchableOpacity>
			) : null}
		</View>
	)
}

const styles = StyleSheet.create({
	chip: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[2],
		backgroundColor: colors.brand.cyanDim,
		borderWidth: 1,
		borderColor: colors.border.cyan,
		borderRadius: radius.pill,
		paddingHorizontal: spacing[3],
		paddingVertical: spacing[1],
		alignSelf: 'flex-start',
	},
	label: {
		flex: 1,
		fontSize: typography.size.xs,
		color: colors.brand.cyan,
		fontWeight: typography.weight.medium,
	},
})
