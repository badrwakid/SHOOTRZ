import React, { useEffect, useRef } from 'react'
import { View, Text, StyleSheet, Animated } from 'react-native'
import { colors, radius, spacing, typography } from '../constants/theme'

interface ProgressBarProps {
	progress: number
	color?: string
	height?: number
	animated?: boolean
	showPercent?: boolean
}

export function ProgressBar({
	progress,
	color = colors.brand.orange,
	height = 6,
	animated = true,
	showPercent = false,
}: ProgressBarProps) {
	const widthAnim = useRef(new Animated.Value(0)).current
	const clamped = Math.max(0, Math.min(1, progress))

	useEffect(() => {
		if (animated) {
			Animated.spring(widthAnim, {
				toValue: clamped,
				useNativeDriver: false,
				damping: 15,
				stiffness: 150,
			}).start()
		} else {
			widthAnim.setValue(clamped)
		}
	}, [clamped, animated])

	const width = widthAnim.interpolate({
		inputRange: [0, 1],
		outputRange: ['0%', '100%'],
	})

	return (
		<View style={styles.row}>
			<View style={[styles.track, { height, borderRadius: height / 2 }]}>
				<Animated.View
					style={[
						styles.fill,
						{
							width,
							height,
							borderRadius: height / 2,
							backgroundColor: color,
						},
					]}
				/>
			</View>
			{showPercent ? (
				<Text style={styles.percent}>{Math.round(clamped * 100)}%</Text>
			) : null}
		</View>
	)
}

const styles = StyleSheet.create({
	row: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[2],
	},
	track: {
		flex: 1,
		backgroundColor: colors.bg.elevated,
		overflow: 'hidden',
	},
	fill: {
		position: 'absolute',
		left: 0,
		top: 0,
	},
	percent: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.semibold,
		color: colors.text.secondary,
		minWidth: 32,
		textAlign: 'right',
	},
})
