import React, { useCallback, useState } from 'react'
import {
	Pressable,
	Text,
	StyleSheet,
	ActivityIndicator,
	ViewStyle,
} from 'react-native'
import { colors, typography } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'
import { FocusRing, defaultFocusRing } from './FocusRing'
import {
	V3_ORANGE,
	V3_DANGER,
	V3_CYAN,
	DISABLED_SLATE,
	SIZE,
	ORANGE_STROKE,
} from './buttonTokens'

type ButtonVariant = 'orange' | 'cyan' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

export interface SecondaryButtonProps {
	label: string
	onPress: () => void
	variant?: ButtonVariant
	size?: ButtonSize
	disabled?: boolean
	loading?: boolean
	fullWidth?: boolean
	style?: ViewStyle
}

export function SecondaryButton({
	label,
	onPress,
	variant = 'orange',
	size = 'md',
	disabled = false,
	loading = false,
	fullWidth = false,
	style,
}: SecondaryButtonProps) {
	const [focused, setFocused] = useState(false)
	const s = SIZE[size]
	const isBlocked = disabled || loading
	const isSlate = disabled
	const showFocus = focused && !isBlocked

	const handlePress = useCallback(() => {
		if (isBlocked) return
		hapticFeedback.light()
		onPress()
	}, [isBlocked, onPress])

	const palette = (pressed: boolean) => {
		if (isSlate) {
			return {
				color: DISABLED_SLATE.label,
				borderColor: colors.border.default,
				backgroundColor: DISABLED_SLATE.bg,
			}
		}
		if (variant === 'ghost') {
			return {
				color: ORANGE_STROKE,
				borderColor: 'transparent',
				backgroundColor: pressed ? 'rgba(187, 63, 21, 0.1)' : 'transparent',
			}
		}
		if (variant === 'danger') {
			return {
				color: V3_DANGER.default,
				borderColor: pressed ? V3_DANGER.pressed : V3_DANGER.default,
				backgroundColor: 'transparent',
			}
		}
		if (variant === 'cyan') {
			return {
				color: V3_CYAN.default,
				borderColor: pressed ? V3_CYAN.pressed : V3_CYAN.default,
				backgroundColor: 'transparent',
			}
		}
		return {
			color: V3_ORANGE.default,
			borderColor: pressed ? V3_ORANGE.pressed : V3_ORANGE.default,
			backgroundColor: 'transparent',
		}
	}

	const borderWidth = variant === 'ghost' ? 0 : 1
	const effBorderW = isSlate ? 1 : borderWidth

	return (
		<FocusRing
			visible={showFocus}
			innerBorderRadius={s.radius}
			token={defaultFocusRing}
			style={fullWidth ? styles.ringFullWidth : undefined}
		>
			<Pressable
				onPress={handlePress}
				disabled={isBlocked}
				accessibilityRole="button"
				accessibilityLabel={label}
				accessibilityState={{ disabled: isBlocked, busy: !!loading }}
				onFocus={() => setFocused(true)}
				onBlur={() => setFocused(false)}
				android_ripple={
					isBlocked
						? undefined
						: { color: 'rgba(255,255,255,0.12)', borderless: false }
				}
				style={({ pressed }) => {
					const c = palette(pressed)
					return [
						styles.base,
						{
							height: s.height,
							borderRadius: s.radius,
							paddingHorizontal: s.px,
							gap: s.gap,
							borderWidth: effBorderW,
						},
						fullWidth && styles.fullWidth,
						{
							backgroundColor: c.backgroundColor,
							borderColor: c.borderColor,
						},
						style,
					]
				}}
			>
				{({ pressed }) =>
					loading ? (
						<ActivityIndicator
							color={isSlate ? DISABLED_SLATE.label : palette(pressed).color}
							size="small"
						/>
					) : (
						<Text
							style={[
								styles.label,
								{
									color: palette(pressed).color,
									fontSize: s.font,
								},
							]}
						>
							{label.toUpperCase()}
						</Text>
					)
				}
			</Pressable>
		</FocusRing>
	)
}

const styles = StyleSheet.create({
	base: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		minWidth: 120,
		overflow: 'hidden',
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
})
