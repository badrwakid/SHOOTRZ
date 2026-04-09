import React, { useCallback } from 'react'
import { TouchableOpacity, Text, StyleSheet, ViewStyle } from 'react-native'
import { colors, radius, typography, spacing } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'

interface SecondaryButtonProps {
	label: string
	onPress: () => void
	variant?: 'outlined' | 'ghost' | 'danger'
	disabled?: boolean
	style?: ViewStyle
}

export function SecondaryButton({
	label,
	onPress,
	variant = 'outlined',
	disabled = false,
	style,
}: SecondaryButtonProps) {
	const handlePress = useCallback(() => {
		if (disabled) return
		hapticFeedback.light()
		onPress()
	}, [disabled, onPress])

	const borderColor =
		variant === 'danger' ? colors.error : colors.brand.orange
	const textColor =
		variant === 'danger' ? colors.error : colors.brand.orange

	return (
		<TouchableOpacity
			onPress={handlePress}
			disabled={disabled}
			activeOpacity={0.85}
			accessibilityRole="button"
			accessibilityLabel={label}
			style={[
				styles.base,
				variant !== 'ghost' && { borderWidth: 1, borderColor },
				disabled && styles.disabled,
				style,
			]}
		>
			<Text style={[styles.label, { color: textColor }]}>
				{label.toUpperCase()}
			</Text>
		</TouchableOpacity>
	)
}

const styles = StyleSheet.create({
	base: {
		height: 48,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		borderRadius: radius.button,
		paddingHorizontal: spacing[6],
		backgroundColor: 'transparent',
	},
	disabled: {
		opacity: 0.4,
	},
	label: {
		fontWeight: typography.weight.bold,
		fontSize: typography.size.sm,
		letterSpacing: typography.tracking.widest,
	},
})
