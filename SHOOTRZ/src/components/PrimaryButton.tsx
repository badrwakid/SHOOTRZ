import React, { useCallback } from 'react'
import {
	TouchableOpacity,
	Text,
	StyleSheet,
	ActivityIndicator,
	ViewStyle,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, radius, typography, spacing, shadows } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'

type ButtonVariant = 'orange' | 'cyan' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

interface PrimaryButtonProps {
	label: string
	onPress: () => void
	loading?: boolean
	disabled?: boolean
	size?: ButtonSize
	variant?: ButtonVariant
	icon?: string
	fullWidth?: boolean
	style?: ViewStyle
}

const HEIGHT: Record<ButtonSize, number> = { sm: 40, md: 48, lg: 56 }

export function PrimaryButton({
	label,
	onPress,
	loading = false,
	disabled = false,
	size = 'md',
	variant = 'orange',
	icon,
	fullWidth = false,
	style,
}: PrimaryButtonProps) {
	const handlePress = useCallback(() => {
		if (loading || disabled) return
		hapticFeedback.medium()
		onPress()
	}, [loading, disabled, onPress])

	const bgColor =
		variant === 'cyan'
			? colors.brand.cyan
			: variant === 'danger'
				? colors.error
				: variant === 'ghost'
					? 'transparent'
					: colors.brand.orange

	const textColor =
		variant === 'ghost' ? colors.brand.orange : colors.text.primary

	const shadowStyle =
		variant === 'orange'
			? shadows.orange
			: variant === 'cyan'
				? shadows.cyan
				: undefined

	return (
		<TouchableOpacity
			onPress={handlePress}
			disabled={disabled || loading}
			activeOpacity={0.85}
			accessibilityRole="button"
			accessibilityLabel={label}
			accessibilityState={{ disabled: disabled || loading }}
			style={[
				styles.base,
				{ height: HEIGHT[size], backgroundColor: bgColor },
				shadowStyle,
				fullWidth && styles.fullWidth,
				variant === 'ghost' && styles.ghost,
				(disabled || loading) && styles.disabled,
				style,
			]}
		>
			{loading ? (
				<ActivityIndicator color={textColor} size="small" />
			) : (
				<>
					{icon ? (
						<Ionicons
							name={icon as any}
							size={size === 'sm' ? 16 : 18}
							color={textColor}
							style={styles.icon}
						/>
					) : null}
					<Text
						style={[
							styles.label,
							{
								color: textColor,
								fontSize: size === 'sm' ? typography.size.xs : typography.size.sm,
							},
						]}
					>
						{label.toUpperCase()}
					</Text>
				</>
			)}
		</TouchableOpacity>
	)
}

const styles = StyleSheet.create({
	base: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		borderRadius: radius.button,
		paddingHorizontal: spacing[6],
		minWidth: 120,
	},
	fullWidth: {
		width: '100%',
	},
	ghost: {
		borderWidth: 1,
		borderColor: colors.brand.orange,
	},
	disabled: {
		opacity: 0.4,
	},
	label: {
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.widest,
	},
	icon: {
		marginRight: spacing[2],
	},
})
