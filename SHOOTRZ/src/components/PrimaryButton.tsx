import React, { useCallback, useState } from 'react'
import {
	Pressable,
	Text,
	StyleSheet,
	ActivityIndicator,
	ViewStyle,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'
import { FocusRing, defaultFocusRing } from './FocusRing'
import {
	V3_ORANGE,
	V3_CYAN,
	V3_DANGER,
	ORANGE_STROKE,
	DISABLED_SLATE,
	SIZE,
} from './buttonTokens'

type ButtonVariant = 'orange' | 'cyan' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

const FILL = {
	orange: V3_ORANGE,
	cyan: V3_CYAN,
	danger: V3_DANGER,
} as const

const shadowForVariant = (variant: ButtonVariant): ViewStyle | undefined => {
	if (variant === 'ghost') {
		return undefined
	}
	if (variant === 'danger') {
		return {
			shadowColor: V3_DANGER.default,
			shadowOffset: { width: 0, height: 4 },
			shadowOpacity: 0.3,
			shadowRadius: 10,
			elevation: 6,
		}
	}
	if (variant === 'cyan') {
		return {
			shadowColor: V3_CYAN.default,
			shadowOffset: { width: 0, height: 4 },
			shadowOpacity: 0.3,
			shadowRadius: 10,
			elevation: 6,
		}
	}
	return {
		shadowColor: V3_ORANGE.default,
		shadowOffset: { width: 0, height: 4 },
		shadowOpacity: 0.3,
		shadowRadius: 10,
		elevation: 6,
	}
}

export interface PrimaryButtonProps {
	label: string
	onPress: () => void
	loading?: boolean
	disabled?: boolean
	size?: ButtonSize
	variant?: ButtonVariant
	icon?: string
	fullWidth?: boolean
	/** Renders a circular/square control with icon or spinner only; `label` is used for a11y unless `a11yLabel` is set. */
	iconOnly?: boolean
	/** Screen reader text when `iconOnly` (or override for `label`). */
	a11yLabel?: string
	style?: ViewStyle
}

export function PrimaryButton({
	label,
	onPress,
	loading = false,
	disabled = false,
	size = 'md',
	variant = 'orange',
	icon,
	fullWidth = false,
	iconOnly = false,
	a11yLabel,
	style,
}: PrimaryButtonProps) {
	const [focused, setFocused] = useState(false)
	const s = SIZE[size]
	const isBlocked = disabled || loading
	const isSlate = disabled && !loading

	const handlePress = useCallback(() => {
		if (isBlocked) return
		hapticFeedback.medium()
		onPress()
	}, [isBlocked, onPress])

	const a11y = a11yLabel ?? label
	const showFocus = focused && !isBlocked
	const textPrimary = colors.text.primary

	const resolveStyle = (pressed: boolean) => {
		if (isSlate) {
			return {
				backgroundColor: DISABLED_SLATE.bg,
				borderColor: colors.border.default,
				borderWidth: 1,
			}
		}
		if (variant === 'ghost') {
			return {
				backgroundColor: pressed
					? 'rgba(187, 63, 21, 0.14)'
					: 'transparent',
				borderColor: ORANGE_STROKE,
				borderWidth: 1,
			}
		}
		const v = FILL[variant as 'orange' | 'cyan' | 'danger']
		return {
			backgroundColor: pressed ? v.pressed : v.default,
			borderWidth: 0,
		}
	}

	const textColor = () => {
		if (isSlate) return DISABLED_SLATE.label
		if (variant === 'ghost') return ORANGE_STROKE
		return textPrimary
	}

	const minWidth = iconOnly ? s.height : 120
	const content = loading ? (
		<ActivityIndicator color={textColor()} size="small" />
	) : iconOnly ? (
		icon ? (
			<Ionicons name={icon as any} size={s.icon} color={textColor()} />
		) : null
	) : (
		<>
			{icon ? (
				<Ionicons
					name={icon as any}
					size={s.icon}
					color={textColor()}
					style={styles.icon}
				/>
			) : null}
			<Text
				style={[
					styles.label,
					{
						color: textColor(),
						fontSize: s.font,
					},
				]}
			>
				{label.toUpperCase()}
			</Text>
		</>
	)

	return (
		<FocusRing
			visible={showFocus}
			innerBorderRadius={iconOnly ? s.height / 2 : s.radius}
			token={defaultFocusRing}
			style={fullWidth && !iconOnly ? styles.ringFullWidth : undefined}
		>
			<Pressable
				onPress={handlePress}
				accessibilityRole="button"
				accessibilityLabel={a11y}
				accessibilityState={{ disabled: isBlocked, busy: !!loading }}
				disabled={isBlocked}
				onFocus={() => setFocused(true)}
				onBlur={() => setFocused(false)}
				android_ripple={
					isBlocked
						? undefined
						: { color: 'rgba(255,255,255,0.2)', borderless: false }
				}
				style={({ pressed }) => [
					styles.base,
					{
						height: s.height,
						minWidth,
						borderRadius: iconOnly ? s.height / 2 : s.radius,
						paddingHorizontal: iconOnly ? 0 : s.px,
						gap: s.gap,
					},
					!isSlate && shadowForVariant(variant),
					fullWidth && !iconOnly && styles.fullWidth,
					resolveStyle(pressed),
					style,
				]}
			>
				{content}
			</Pressable>
		</FocusRing>
	)
}

const styles = StyleSheet.create({
	base: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
	},
	fullWidth: {
		width: '100%',
		alignSelf: 'stretch',
	},
	ringFullWidth: {
		alignSelf: 'stretch',
		width: '100%',
	},
	label: {
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.widest,
	},
	icon: {
		marginRight: spacing[2],
	},
})
