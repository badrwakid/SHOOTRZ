import React from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { spacing } from '../constants/theme'
import { useTokens } from '../theme/useTokens'

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
	const t = useTokens()

	return (
		<View
			style={[
				styles.header,
				!transparent && [styles.opaque, { backgroundColor: t.tokens.bg.primary, borderBottomColor: t.tokens.border.subtle }],
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
					<Ionicons name="chevron-back" size={24} color={t.tokens.text.primary} />
				</TouchableOpacity>
			) : (
				<View style={styles.backPlaceholder} />
			)}
			<View style={styles.center}>
				<Text style={[t.typography.headingMd, { color: t.tokens.text.primary }]} numberOfLines={1}>
					{title}
				</Text>
				{subtitle ? (
					<Text
						style={[
							t.typography.caption,
							{ color: t.tokens.text.secondary, marginTop: spacing[1] },
						]}
						numberOfLines={1}
					>
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
		borderBottomWidth: 1,
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
	rightAction: {
		width: 44,
		alignItems: 'flex-end',
	},
})
