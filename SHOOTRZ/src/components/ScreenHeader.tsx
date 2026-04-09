import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing } from '../constants/theme'

interface ScreenHeaderProps {
	title: string
	subtitle?: string
	backButton?: () => void
	rightAction?: React.ReactNode
	transparent?: boolean
}

export function ScreenHeader({
	title,
	subtitle,
	backButton,
	rightAction,
	transparent = false,
}: ScreenHeaderProps) {
	return (
		<View
			style={[
				styles.header,
				!transparent && styles.opaque,
			]}
		>
			{backButton ? (
				<TouchableOpacity
					onPress={backButton}
					style={styles.back}
					accessibilityRole="button"
					accessibilityLabel="Go back"
					hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
				>
					<Ionicons name="chevron-back" size={24} color={colors.text.primary} />
				</TouchableOpacity>
			) : (
				<View style={styles.backPlaceholder} />
			)}
			<View style={styles.center}>
				<Text style={styles.title} numberOfLines={1}>
					{title}
				</Text>
				{subtitle ? (
					<Text style={styles.subtitle} numberOfLines={1}>
						{subtitle}
					</Text>
				) : null}
			</View>
			{rightAction ? (
				<View style={styles.rightAction}>{rightAction}</View>
			) : (
				<View style={styles.backPlaceholder} />
			)}
		</View>
	)
}

const styles = StyleSheet.create({
	header: {
		height: spacing.headerHeight,
		flexDirection: 'row',
		alignItems: 'center',
		paddingHorizontal: spacing.screenPadding,
	},
	opaque: {
		backgroundColor: colors.bg.primary,
		borderBottomWidth: 1,
		borderBottomColor: colors.border.subtle,
	},
	back: {
		width: 44,
		height: 44,
		alignItems: 'center',
		justifyContent: 'center',
	},
	backPlaceholder: {
		width: 44,
	},
	center: {
		flex: 1,
		alignItems: 'center',
	},
	title: {
		fontSize: typography.size.lg,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
	},
	subtitle: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
	},
	rightAction: {
		width: 44,
		alignItems: 'flex-end',
	},
})
