import React, { useEffect, useRef } from 'react'
import { View, Text, StyleSheet, Animated } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, animation } from '../constants/theme'
import { PrimaryButton } from './PrimaryButton'

interface EmptyStateProps {
	icon: string
	title: string
	message: string
	actionText?: string
	onAction?: () => void
	action?: { label: string; onPress: () => void }
}

export const EmptyState: React.FC<EmptyStateProps> = ({
	icon,
	title,
	message,
	actionText,
	onAction,
	action,
}) => {
	const fadeAnim = useRef(new Animated.Value(0)).current
	const slideAnim = useRef(new Animated.Value(20)).current

	useEffect(() => {
		Animated.parallel([
			Animated.timing(fadeAnim, {
				toValue: 1,
				duration: animation.duration.slow,
				useNativeDriver: true,
			}),
			Animated.timing(slideAnim, {
				toValue: 0,
				duration: animation.duration.slow,
				useNativeDriver: true,
			}),
		]).start()
	}, [])

	const resolvedAction = action ?? (actionText && onAction ? { label: actionText, onPress: onAction } : null)

	return (
		<Animated.View
			style={[
				styles.container,
				{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
			]}
		>
			<Ionicons name={icon as any} size={64} color={colors.brand.chrome} />
			<Text style={styles.title}>{title}</Text>
			<Text style={styles.message}>{message}</Text>
			{resolvedAction ? (
				<PrimaryButton
					label={resolvedAction.label}
					onPress={resolvedAction.onPress}
					style={styles.actionButton}
				/>
			) : null}
		</Animated.View>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		justifyContent: 'center',
		alignItems: 'center',
		padding: spacing[8],
	},
	title: {
		fontSize: typography.size.lg,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
		textAlign: 'center',
		marginTop: spacing[4],
	},
	message: {
		fontSize: typography.size.base,
		color: colors.text.secondary,
		textAlign: 'center',
		maxWidth: 280,
		marginTop: spacing[2],
		lineHeight: typography.size.base * typography.lineHeight.normal,
	},
	actionButton: {
		marginTop: spacing[6],
	},
})
