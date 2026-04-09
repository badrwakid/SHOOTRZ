import React, { useEffect, useRef } from 'react'
import { View, StyleSheet, Animated } from 'react-native'
import { colors, spacing, radius, glass } from '../constants/theme'

export function TypingIndicator() {
	const dots = useRef([
		new Animated.Value(0.3),
		new Animated.Value(0.3),
		new Animated.Value(0.3),
	]).current

	useEffect(() => {
		const anims = dots.map((dot, i) =>
			Animated.loop(
				Animated.sequence([
					Animated.delay(i * 150),
					Animated.timing(dot, {
						toValue: 1,
						duration: 350,
						useNativeDriver: true,
					}),
					Animated.timing(dot, {
						toValue: 0.3,
						duration: 350,
						useNativeDriver: true,
					}),
				]),
			),
		)
		anims.forEach(a => a.start())
		return () => anims.forEach(a => a.stop())
	}, [dots])

	return (
		<View style={styles.row}>
			<View style={styles.avatar}>
				<Animated.Text style={styles.avatarText}>J</Animated.Text>
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
		fontSize: 13,
		fontWeight: '700',
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
