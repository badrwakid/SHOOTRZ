import React, { useCallback } from 'react'
import { TouchableOpacity, View, Text, StyleSheet } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, radius, spacing, typography } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'

interface IconButtonProps {
	icon: string
	onPress: () => void
	size?: number
	color?: string
	badge?: number
	style?: any
}

export function IconButton({
	icon,
	onPress,
	size = 40,
	color = colors.text.primary,
	badge,
	style,
}: IconButtonProps) {
	const handlePress = useCallback(() => {
		hapticFeedback.light()
		onPress()
	}, [onPress])

	return (
		<TouchableOpacity
			onPress={handlePress}
			activeOpacity={0.85}
			accessibilityRole="button"
			style={[
				styles.base,
				{ width: size, height: size, borderRadius: size / 2 },
				style,
			]}
		>
			<Ionicons name={icon as any} size={size * 0.5} color={color} />
			{badge != null && badge > 0 ? (
				<View style={styles.badge}>
					<Text style={styles.badgeText}>
						{badge > 99 ? '99+' : badge}
					</Text>
				</View>
			) : null}
		</TouchableOpacity>
	)
}

const styles = StyleSheet.create({
	base: {
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: colors.bg.elevated,
	},
	badge: {
		position: 'absolute',
		top: -2,
		right: -2,
		minWidth: 18,
		height: 18,
		borderRadius: 9,
		backgroundColor: colors.brand.orange,
		alignItems: 'center',
		justifyContent: 'center',
		paddingHorizontal: spacing[1],
	},
	badgeText: {
		color: colors.text.primary,
		fontSize: typography.size.xs,
		fontWeight: typography.weight.bold,
	},
})
