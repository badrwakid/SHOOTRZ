import React, { useEffect, useRef } from 'react'
import { View, Text, StyleSheet, Animated } from 'react-native'
import { colors, typography, spacing, radius, glass } from '../constants/theme'
import { useReduceMotion } from '../hooks/useReduceMotion'
import { motion } from '../theme/motion'

interface ChatBubbleProps {
	message: string
	role: 'user' | 'coach'
	timestamp?: string
	streaming?: boolean
}

export function ChatBubble({ message, role, timestamp, streaming }: ChatBubbleProps) {
	const isUser = role === 'user'
	const reduceMotion = useReduceMotion()
	const cursorOpacity = useRef(new Animated.Value(1)).current

	useEffect(() => {
		if (!streaming) {
			cursorOpacity.setValue(1)
			return
		}
		if (reduceMotion) {
			cursorOpacity.setValue(1)
			return
		}
		const loop = Animated.loop(
			Animated.sequence([
				Animated.timing(cursorOpacity, {
					toValue: 0.15,
					duration: motion.timing.fast,
					useNativeDriver: true,
				}),
				Animated.timing(cursorOpacity, {
					toValue: 1,
					duration: motion.timing.fast,
					useNativeDriver: true,
				}),
			]),
		)
		loop.start()
		return () => {
			loop.stop()
			cursorOpacity.setValue(1)
		}
	}, [streaming, reduceMotion, cursorOpacity])

	return (
		<View style={[styles.row, isUser ? styles.rowUser : styles.rowCoach]}>
			{!isUser ? (
				<View style={styles.avatar}>
					<Text style={styles.avatarText}>J</Text>
				</View>
			) : null}
			<View style={isUser ? styles.bubbleUser : styles.bubbleCoach}>
				<Text style={styles.text}>
					{message}
					{streaming ? (
						<Animated.Text
							style={[styles.cursor, { opacity: cursorOpacity }]}
							accessible={false}
							importantForAccessibility="no"
							accessibilityElementsHidden
						>
							|
						</Animated.Text>
					) : null}
				</Text>
				{timestamp ? <Text style={styles.time}>{timestamp}</Text> : null}
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
	rowUser: {
		justifyContent: 'flex-end',
	},
	rowCoach: {
		justifyContent: 'flex-start',
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
	bubbleUser: {
		maxWidth: '80%',
		backgroundColor: colors.chat.userBubble,
		borderWidth: 1,
		borderColor: colors.chat.userBorder,
		borderTopLeftRadius: radius.xl,
		borderTopRightRadius: radius.xl,
		borderBottomLeftRadius: radius.xl,
		borderBottomRightRadius: radius.xs,
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
	},
	bubbleCoach: {
		maxWidth: '80%',
		backgroundColor: glass.cyan.bg,
		borderWidth: 1,
		borderColor: glass.cyan.border,
		borderTopLeftRadius: radius.xl,
		borderTopRightRadius: radius.xl,
		borderBottomLeftRadius: radius.xs,
		borderBottomRightRadius: radius.xl,
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
	},
	text: {
		fontSize: typography.size.base,
		color: colors.text.primary,
		lineHeight: typography.size.base * typography.lineHeight.normal,
	},
	cursor: {
		color: colors.brand.cyan,
		fontWeight: typography.weight.bold,
	},
	time: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
		marginTop: spacing[1],
		alignSelf: 'flex-end',
	},
})
