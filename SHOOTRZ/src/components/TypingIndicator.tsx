import React, { useEffect, useRef } from 'react'
import { View, Text, StyleSheet, Animated } from 'react-native'
import { colors, spacing, radius, glass, typography } from '../constants/theme'
import { useReduceMotion } from '../hooks/useReduceMotion'
import { motion } from '../theme/motion'

export function TypingIndicator() {
	const reduceMotion = useReduceMotion()
	const dots = useRef([
		new Animated.Value(0.3),
		new Animated.Value(0.3),
		new Animated.Value(0.3),
	]).current
	const { stagger, typingPulse } = motion.timing

	useEffect(() => {
		if (reduceMotion) {
			dots.forEach(d => d.setValue(1))
			return
		}
		const anims = dots.map((dot, i) =>
			Animated.loop(
				Animated.sequence([
					Animated.delay(i * stagger),
					Animated.timing(dot, {
						toValue: 1,
						duration: typingPulse,
						useNativeDriver: true,
					}),
					Animated.timing(dot, {
						toValue: 0.3,
						duration: typingPulse,
						useNativeDriver: true,
					}),
				]),
			),
		)
		anims.forEach(a => a.start())
		return () => anims.forEach(a => a.stop())
	}, [dots, reduceMotion, stagger, typingPulse])

	return (
		<View
			style={styles.row}
			accessible
			accessibilityRole="text"
			accessibilityLabel="Coach is typing"
			accessibilityState={{ busy: true }}
		>
			<View style={styles.avatar}>
				<Text style={styles.avatarText}>J</Text>
			</View>
			<View style={styles.bubble}>
				{dots.map((opacity, i) => (
					<Animated.View key={i} style={[styles.dot, { opacity }]} />
				))}
			</View>
		</View>
	)
}

const styles = StyleSheet.create({
	row: {
		flexDirection: 'row',
		alignItems: 'flex-end',
		marginBottom: spacing[2],
	},
	avatar: {
		width: 32,
		height: 32,
		borderRadius: 16,
		backgroundColor: colors.brand.cyan,
		alignItems: 'center',
		justifyContent: 'center',
		marginRight: spacing[2],
	},
	avatarText: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.bold,
		color: colors.bg.primary,
	},
	bubble: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: 5,
		backgroundColor: glass.cyan.bg,
		borderWidth: 1,
		borderColor: glass.cyan.border,
		borderRadius: radius.xl,
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
	},
	dot: {
		width: 8,
		height: 8,
		borderRadius: 4,
		backgroundColor: colors.brand.cyan,
	},
})
